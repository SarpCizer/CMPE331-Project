import { useEffect, useRef, useState } from 'react';

const colors=['#174c3a','#537e59','#885536','#486548','#315f50','#6e592b'];
export default function SurpriseWheel({ api, run, busy, openRecipe }) {
  const [recipes,setRecipes]=useState([]),[selected,setSelected]=useState(null),[spinning,setSpinning]=useState(false),[rotation,setRotation]=useState(0),[loaded,setLoaded]=useState(false),[notice,setNotice]=useState('');
  const alive=useRef(true),timer=useRef(null),angle=useRef(0),lock=useRef(false);
  useEffect(()=>{alive.current=true;return()=>{alive.current=false;clearTimeout(timer.current);};},[]);
  async function refresh(){
    const items=await run(()=>api('/surprise-recipes'),'');
    if(Array.isArray(items)&&alive.current){setRecipes(items);setLoaded(true);setSelected(null);setNotice('');}
  }
  async function spin(){
    if(lock.current)return;
    lock.current=true;
    const items=await run(()=>api('/surprise-recipes'),'');
    if(!alive.current){lock.current=false;return;}
    if(!Array.isArray(items)){lock.current=false;return;}
    setRecipes(items);setLoaded(true);setSelected(null);setNotice('');
    if(!items.length){lock.current=false;return;}
    const values=new Uint32Array(1);crypto.getRandomValues(values);
    const index=Math.floor(values[0]/4294967296*items.length);
    const target=360-(index+.5)*360/items.length;
    angle.current+=1080+((target-angle.current%360+360)%360);
    setRotation(angle.current);setSpinning(true);
    const finish=async()=>{
      const fresh=await run(()=>api('/surprise-recipes'),'');
      if(alive.current){
        if(Array.isArray(fresh)){const chosen=fresh.find(item=>item.id===items[index].id);setSelected(chosen||null);if(!chosen){setRecipes(fresh);setNotice('Your fridge changed. Spin again with the updated recipes.');}}else setNotice('The final fridge check failed. Please try again.');
        setSpinning(false);
      }
      lock.current=false;
    };
    timer.current=setTimeout(finish,matchMedia('(prefers-reduced-motion: reduce)').matches?0:2200);
  }
  const gradient=recipes.length?`conic-gradient(${recipes.map((_,i)=>`${colors[i%colors.length]} ${i*360/recipes.length}deg ${(i+1)*360/recipes.length}deg`).join(',')})`:'#e5ece2';
  return <section className="panel mt-6" aria-label="Surprise me recipe wheel">
    <span className="eyebrow">LET YOUR FRIDGE DECIDE</span><h2>Surprise me.</h2>
    <p>A little spin, a good meal. Only saved recipes fully covered by your current measured fridge stock enter the wheel. Spinning uses no AI requests and does not use up ingredients.</p>
    <div className="flex flex-wrap items-center gap-8">
      <div className="relative mx-auto h-[260px] w-[260px] shrink-0" aria-hidden="true">
        <div className="absolute left-1/2 top-0 z-10 -translate-x-1/2 text-3xl text-[#b57950]">▼</div>
        <div className="h-full w-full rounded-full border-8 border-[#e5ece2] shadow-inner" style={{background:gradient,transform:`rotate(${rotation}deg)`,transition:spinning&&!matchMedia('(prefers-reduced-motion: reduce)').matches?'transform 2.2s cubic-bezier(.15,.7,.15,1)':undefined}}>
          {recipes.map((recipe,i)=><span key={recipe.id} className="absolute left-1/2 top-1/2 text-xs font-semibold text-white" style={{transform:`rotate(${(i+.5)*360/recipes.length-90}deg) translateX(38px)`,width:76,overflow:'hidden',whiteSpace:'nowrap',textOverflow:'ellipsis'}}>{recipes.length>12?i+1:recipe.title}</span>)}
        </div>
      </div>
      <div className="min-w-0 flex-1">
        <button type="button" className="btn-primary" disabled={busy||spinning} onClick={spin}>{spinning?'Choosing your meal…':'Spin the wheel'}</button>
        <button type="button" className="btn-text ml-3" disabled={busy||spinning} onClick={refresh}>Refresh wheel recipes</button>
        <div role="status" aria-live="polite" className="mt-4">
          {notice?<p>{notice}</p>:selected?<><h3>{selected.title}</h3><p>{selected.servings} portions · {selected.cookingMinutes} min (estimate)</p><button type="button" className="btn-secondary" disabled={busy||spinning} onClick={()=>openRecipe(selected.id)}>View selected recipe</button></>:loaded&&!recipes.length?<p>No fully stocked recipes yet. Generate recipes above or restock ingredients. Unknown amounts must be measured before a recipe can enter the wheel.</p>:spinning?<p>Checking your fridge and picking a recipe…</p>:<p>{loaded?`${recipes.length} recipes ready to spin.`:'Spin to load recipes from your fridge.'}</p>}
        </div>
        {recipes.length>0&&<details className="mt-4"><summary>Recipes on the wheel ({recipes.length})</summary><ul className="list-disc pl-5">{recipes.map(item=><li key={item.id}>{item.title}</li>)}</ul></details>}
      </div>
    </div>
  </section>;
}
