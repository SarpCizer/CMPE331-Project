import { test, expect } from './fixtures.js';
import AxeBuilder from '@axe-core/playwright';
const titles=['Wheel eggplant rice','Wheel baked potatoes','Wheel banana smoothie'];

async function kitchen(page) {
 const credentials={email:`wheel-${crypto.randomUUID()}@example.test`,password:'Isolated-wheel-fixture-123!'};
 await page.request.post('/api/accounts',{data:credentials});
 const {token}=await(await page.request.post('/api/sessions',{data:credentials})).json();
 const headers={Authorization:`Bearer ${token}`};
 await page.request.post('/api/inventory',{headers,data:{name:'milk',quantity:200,unit:'ml'}});
 const historical=await(await page.request.post('/api/recipes/generate',{headers,data:{}})).json();
 expect(historical[0].title).toBe('Warm milk');
 for(const [name,quantity,unit] of [['banana',2,'pcs'],['rice',500,'g'],['eggplant',1,'pcs'],['potatoes',500,'g'],['salt',1,'pack'],['wheel-fixture',1,'pcs']]) {
  await page.request.post('/api/inventory',{headers,data:{name,quantity,unit}});
 }
 const stock=await(await page.request.get('/api/inventory',{headers})).json();
 await page.goto('/');
 await page.evaluate(s=>sessionStorage.setItem('fridgely.session',JSON.stringify(s)),{token,email:credentials.email});
 await page.goto('/#/recipes'); await page.reload();
 return {headers,stock};
}
async function generate(page) {
 const response=page.waitForResponse(r=>r.url().endsWith('/api/recipes/generate')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Generate recipes',exact:true}).click();
 const recipes=await(await response).json();
 expect(recipes.map(recipe=>recipe.title)).toEqual(titles);
 for(const title of titles) await expect(page.getByRole('heading',{name:title,exact:true})).toBeVisible();
 return recipes;
}
for(const width of [360,1440]) test(`wheel includes all three displayed cards, including manual quantities, at ${width}`,async({page})=>{
 await page.setViewportSize({width,height:1000});
 await page.emulateMedia({reducedMotion:'reduce'});
 const {headers,stock}=await kitchen(page);
 const displayed=await generate(page);
 const wheel=page.getByRole('region',{name:'Surprise me recipe wheel'});
 await wheel.getByRole('button',{name:'Spin the wheel',exact:true}).click();
 await expect(wheel.getByRole('heading',{level:3})).toBeVisible();
 await expect(wheel.locator('li')).toHaveText(titles);
 await expect(wheel.locator('summary')).toContainText('(3)');
 await expect(wheel).not.toContainText('Warm milk');
 const selected=await wheel.getByRole('heading',{level:3}).innerText();
 const selectedId=displayed.find(recipe=>recipe.title===selected).id;
 const detail=page.waitForRequest(r=>r.url().endsWith(`/api/recipes/${selectedId}`));
 await wheel.getByRole('button',{name:'View selected recipe'}).click(); await detail;
 await expect(page.getByRole('dialog')).toContainText(selected);
 await page.getByRole('button',{name:'Close recipe',exact:true}).click();
 expect(await(await page.request.get('/api/inventory',{headers})).json()).toEqual(stock);
 expect((await new AxeBuilder({page}).include('main').analyze()).violations).toEqual([]);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('wheel loads every current card immediately, makes no wheel/provider requests, and resets with results',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});
 await kitchen(page);
 let generationRequests=0, wheelRequests=0;
 page.on('request',r=>{if(r.url().endsWith('/api/recipes/generate'))generationRequests++;if(r.url().includes('/surprise-recipes'))wheelRequests++;});
 const wheel=page.getByRole('region',{name:'Surprise me recipe wheel'});
 await expect(wheel.getByRole('button',{name:'Spin the wheel',exact:true})).toBeDisabled();
 await generate(page);
 await expect(wheel.locator('li')).toHaveText(titles);
 for(let spin=0;spin<3;spin++) {
  await wheel.getByRole('button',{name:'Spin the wheel',exact:true}).click();
  await expect(wheel.getByRole('button',{name:'View selected recipe'})).toBeVisible();
 }
 expect(generationRequests).toBe(1); expect(wheelRequests).toBe(0);
 await generate(page);
 await expect(wheel.getByRole('button',{name:'View selected recipe'})).toHaveCount(0);
 await expect(wheel.locator('li')).toHaveText(titles);
 await page.getByRole('button',{name:/Quick & Easy/}).click();
 await expect(wheel.getByRole('button',{name:'Spin the wheel',exact:true})).toBeDisabled();
 await expect(wheel.locator('li')).toHaveCount(0);
});
