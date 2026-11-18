import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, readdir, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { resolve, dirname, extname, relative, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const root = fileURLToPath(new URL('../../', import.meta.url));
const screenshotDir = process.env.ANALYSIS_SCREENSHOTS;
const candidates = [process.env.ANALYSIS_BROWSER, chromium.executablePath(),
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe'].filter(Boolean);
const executablePath = candidates.find(existsSync);
if (!executablePath) throw new Error('Set ANALYSIS_BROWSER to Chromium/Edge/Chrome, or install Playwright Chromium.');
const mime = {'.mjs':'text/javascript','.js':'text/javascript','.html':'text/html','.css':'text/css',
  '.svg':'image/svg+xml','.json':'application/json'};
const server = createServer(async (req,res) => {
  try {
    if (req.url==='/__diagram') {
      res.setHeader('Content-Type','text/html');
      res.end(`<!doctype html><html><head><meta charset="utf-8"><style>body{margin:20px;background:white}svg{height:auto}</style></head><body><div id="diagram"></div><script type="module">
      import mermaid from '/scripts/analysis/node_modules/mermaid/dist/mermaid.esm.min.mjs';
      mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'base',themeVariables:{fontFamily:'Segoe UI, Arial, sans-serif',fontSize:'16px',primaryColor:'#edf4ef',primaryTextColor:'#183c2c',primaryBorderColor:'#658a71',lineColor:'#587267',secondaryColor:'#f8f3e7',tertiaryColor:'#f1f4f1'},flowchart:{htmlLabels:false,useMaxWidth:false},sequence:{useMaxWidth:false},er:{useMaxWidth:false},class:{useMaxWidth:false}});
      window.draw=async(code,dfd=false)=>{
        const result=await mermaid.render('analysisDiagram',code);
        document.getElementById('diagram').innerHTML=result.svg;
        // Opaque label backgrounds keep routed edges from crossing the words.
        for(const rect of document.querySelectorAll('#diagram svg .edgeLabel rect')){
          rect.style.setProperty('opacity','1','important');
          rect.style.setProperty('fill','#fffdf7','important');
        }
        if(dfd){
          // Yourdon-DeMarco stores have parallel lines. Mermaid is only the layout engine.
          for(const group of document.querySelectorAll('#diagram svg g.node.dfdstore')){
            const rect=group.querySelector('rect');
            if(!rect)throw new Error('Data store has no layout rectangle');
            const x=Number(rect.getAttribute('x')),y=Number(rect.getAttribute('y'));
            const w=Number(rect.getAttribute('width')),h=Number(rect.getAttribute('height'));
            rect.style.setProperty('stroke','none','important');
            for(const cy of [y,y+h]){
              const line=document.createElementNS('http://www.w3.org/2000/svg','line');
              for(const [key,value] of Object.entries({x1:x,x2:x+w,y1:cy,y2:cy}))line.setAttribute(key,value);
              line.style.setProperty('stroke','#4d6959','important');
              line.style.setProperty('stroke-width','2px','important');
              group.insertBefore(line,group.querySelector('g.label'));
            }
            group.setAttribute('data-dfd-kind','store');
          }
        }
        return new XMLSerializer().serializeToString(document.querySelector('#diagram svg'));
      };
      window.diagramReady=true;
      </script></body></html>`);
      return;
    }
    const pathname = decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    const path = resolve(root,'.'+pathname);
    if (relative(root,path).startsWith('..')) {res.writeHead(403);res.end();return;}
    const target=(await stat(path)).isDirectory()?join(path,'index.html'):path;
    res.setHeader('Content-Type',mime[extname(target)] || 'application/octet-stream');
    res.end(await readFile(target));
  } catch {res.writeHead(404);res.end('Not found');}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;
try {
  browser=await chromium.launch({executablePath,headless:true});
  const page=await browser.newPage({viewport:{width:1800,height:1200},deviceScaleFactor:2});
  page.on('pageerror',e=>console.error('Browser error:',e.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/__diagram`);
  await page.waitForFunction(()=>window.diagramReady);
  let count=0;
  const manifest=[];
  for (const folder of ['docs/analysis/data','docs/analysis/behavior']) {
    const directory=join(root,folder);
    await mkdir(join(directory,'images'),{recursive:true});
    for (const name of (await readdir(directory)).filter(n=>n.endsWith('.mmd')||n.endsWith('.dfd.json')).sort()) {
      const source=await readFile(join(directory,name),'utf8');
      const isDfd=name.endsWith('.dfd.json');
      let code=source;
      if(isDfd){
        const model=JSON.parse(source);
        const label=value=>value.replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('|','&#124;').replaceAll('\n','<br/>');
        const layout=model.layout || {};
        if(Object.entries(layout).some(([key,value])=>!['nodeSpacing','rankSpacing'].includes(key)||!Number.isFinite(value)||value<20||value>300))throw new Error('Invalid DFD layout options');
        code=(model.layout?'%%{init: '+JSON.stringify({flowchart:layout})+'}%%\n':'')+'flowchart LR\n'+model.nodes.map(node=>{
          const text=label(node.label);
          return node.kind==='process'?`${node.id}(("${text}")):::dfdprocess`:
            `${node.id}["${text}"]:::${node.kind==='store'?'dfdstore':'dfdexternal'}`;
        }).join('\n')+'\n'+model.flows.map(flow=>`${flow.from} -->|"${label(flow.label)}"| ${flow.to}`).join('\n')+
        '\nclassDef dfdprocess fill:#e9f1eb,stroke:#416a50,stroke-width:2px;\nclassDef dfdexternal fill:#f7f7f0,stroke:#6a766b,stroke-width:1.5px;\nclassDef dfdstore fill:#fff9e9,stroke:#4d6959,stroke-width:1.5px;';
      }
      const svg=await page.evaluate(async ({code,isDfd})=>window.draw(code,isDfd),{code,isDfd});
      if (!svg.includes('<svg')) throw new Error('No rendered SVG: '+name);
      const output=svg+'\n';
      const stem=name.replace(/(\.mmd|\.dfd\.json)$/,'');
      const imagePath=join(directory,'images',stem+'.svg');
      await writeFile(imagePath,output);
      const digest=text=>createHash('sha256').update(text.replaceAll('\r\n','\n')).digest('hex');
      manifest.push({source:relative(root,join(directory,name)).replaceAll('\\','/'),svg:relative(root,imagePath).replaceAll('\\','/'),kind:isDfd?'DFD':'data-model',source_sha256:digest(source),svg_sha256:digest(output)});
      if(screenshotDir){await mkdir(screenshotDir,{recursive:true});await page.locator('#diagram svg').screenshot({path:join(screenshotDir,stem+'.png')});}
      count++;
      console.log('Rendered',folder+'/'+name);
    }
  }
  await writeFile(join(root,'docs/analysis/render-manifest.json'),JSON.stringify({diagrams:manifest},null,2)+'\n');
  console.log(`Rendered ${count} data/DFD diagrams with typed-node sources and source/image hashes.`);
} finally {if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
