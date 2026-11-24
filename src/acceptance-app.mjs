import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

/** Connect the approved acceptance cases to real FastAPI routes and SQL storage. */
export async function createAcceptanceApp({recipeProvider, clock = () => new Date().toISOString()} = {}) {
  const root = fileURLToPath(new URL('../', import.meta.url));
  const worker = spawn(process.env.FRIDGELY_PYTHON || 'python3', ['-m','fridgely_app.acceptance'], {
    cwd:root, stdio:['pipe','pipe','pipe'], env:{...process.env,
      PYTHONPATH:[path.join(root,'backend','src'),process.env.PYTHONPATH].filter(Boolean).join(path.delimiter)},
  });
  let counter = 0, stderr = '', tail = Promise.resolve(), closed = false;
  const pending = new Map();
  let resolveReady, rejectReady;
  const ready = new Promise((resolve,reject) => {resolveReady=resolve; rejectReady=reject;});
  const send = message => worker.stdin.write(`${JSON.stringify(message)}\n`);
  const lines = createInterface({input:worker.stdout});
  worker.stderr.on('data', chunk => {stderr=(stderr+chunk).slice(-2000);});
  worker.on('error', error => rejectReady(error));
  worker.on('exit', code => {
    if (!closed) {
      const error = new Error(`FastAPI test worker exited (${code}). Check FRIDGELY_PYTHON and installed backend dependencies. ${stderr}`);
      rejectReady(error);
      for (const task of pending.values()) task.reject(error);
      pending.clear();
    }
  });
  lines.on('line', async line => {
    let message;
    try {message=JSON.parse(line);} catch {return;}
    if (message.kind === 'ready') resolveReady();
    if (message.kind === 'provider') {
      try {
        const value = await recipeProvider.generate(message.input);
        send({kind:'provider-result',ok:true,value});
      } catch {send({kind:'provider-result',ok:false});}
    }
    if (message.kind === 'response') {
      const task = pending.get(message.id);
      pending.delete(message.id);
      task?.resolve({status:message.status,body:message.body});
    }
  });
  const startupTimer = setTimeout(() => {worker.kill(); rejectReady(new Error('FastAPI test worker startup timed out'));},15000);
  try {await ready;} finally {clearTimeout(startupTimer);}
  return {
    request(request) {
      const run = () => new Promise((resolve,reject) => {
        const id = ++counter;
        const timer = setTimeout(() => {pending.delete(id); worker.kill(); reject(new Error('FastAPI request timed out'));},45000);
        pending.set(id,{resolve:value=>{clearTimeout(timer);resolve(value);},reject:error=>{clearTimeout(timer);reject(error);}});
        send({kind:'request',id,now:clock(),request});
      });
      const result = tail.then(run);
      tail = result.catch(() => {});
      return result;
    },
    async close() {
      await tail;
      closed = true;
      send({kind:'close'});
      const timer = setTimeout(() => worker.kill(),5000);
      await new Promise(resolve => worker.once('exit',resolve));
      clearTimeout(timer);
      lines.close();
    },
  };
}

