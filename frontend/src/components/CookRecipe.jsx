import { useState } from 'react';
import { cookingQuantity } from '../utils/cooking';

export default function CookRecipe({ recipe, inventory, run, api, busy, refreshInventory, onCancel, onComplete }) {
  const [rows, setRows] = useState(() => recipe.ingredients.map((name, index) => {
    const matches = inventory.filter(item => item.name.trim().toLowerCase() === name.trim().toLowerCase());
    const item = matches.find(item => item.quantity > 0) || matches[0];
    return { name, measurement: recipe.ingredientAmounts?.[index], matches,
      id: item?.id || '', amount: item ? cookingQuantity(recipe.ingredientAmounts?.[index], item.unit) : '' };
  }));
  const [validation, setValidation] = useState('');
  function change(index, changes) {
    setRows(value => value.map((row, i) => i === index ? { ...row, ...changes } : row));
    setValidation('');
  }
  async function confirm(event) {
    event.preventDefault();
    const items = [];
    for (const row of rows) {
      const item = inventory.find(item => item.id === row.id);
      if (!item || item.quantity == null || item.quantity === 0) continue;
      const quantity = Number(row.amount);
      if (row.amount.trim() === '' || !Number.isFinite(quantity) || quantity < 0 || quantity > item.quantity ||
          (['pcs', 'pack', 'bunch'].includes(item.unit) && !Number.isInteger(quantity))) {
        setValidation('Review each amount: enter a valid quantity within your stock, or 0 to skip.');
        return;
      }
      if (quantity > 0) items.push({ inventoryId: item.id, quantity, unit: item.unit });
    }
    if (!items.length) { setValidation('Choose at least one stocked ingredient to deduct.'); return; }
    // Retain the same request after a lost response, including dialog close/reload.
    const storageKey = `fridgely.cooking.${recipe.id}.${JSON.stringify(items)}`;
    const requestId = sessionStorage.getItem(storageKey) || crypto.randomUUID();
    sessionStorage.setItem(storageKey, requestId);
    const result = await run(async () => {
      try {
        return await api(`/recipes/${recipe.id}/cook`, { method: 'POST', body: { requestId, items } });
      } catch (error) {
        if (error.status === 409) {
          await refreshInventory();
          throw new Error('Stock changed or is insufficient. Review the quantities and try again.');
        }
        throw error;
      }
    }, 'Recipe cooked. Fridge quantities updated.', ['inventory']);
    if (result) { sessionStorage.removeItem(storageKey); onComplete(); }
  }
  return <form noValidate onSubmit={confirm} className="my-5 rounded-xl border border-line p-4">
    <h3>Confirm ingredients used</h3>
    <p>Amounts below are for the full recipe ({recipe.servings} servings). Review what you actually used. Enter 0 to skip an ingredient. Only listed fridge stock is deducted.</p>
    {rows.map((row, index) => {
      const item = inventory.find(item => item.id === row.id);
      return <div key={index} className="my-4">
        <strong>{row.name}{row.measurement ? ` · Recipe: ${row.measurement}` : ''}</strong>
        {row.matches.length > 1 && <><label htmlFor={`stock-${index}`}>Fridge entry for {row.name}</label>
          <select id={`stock-${index}`} value={row.id} onChange={event => {
            const selected = inventory.find(item => item.id === event.target.value);
            change(index, { id: selected.id, amount: cookingQuantity(row.measurement, selected.unit) });
          }}>{row.matches.map(item => <option key={item.id} value={item.id}>{item.name} · {item.quantity ?? 'Unknown'} {item.unit}</option>)}</select></>}
        {!item || item.quantity === 0 ? <p>Not in stock — no deduction.</p> : item.quantity == null ?
          <p>Stock amount unknown. Set its quantity in My Fridge before deducting.</p> : <>
            <label htmlFor={`used-${index}`}>Used {row.name} ({item.unit})</label>
            <input id={`used-${index}`} type="number" min="0" max={item.quantity} step={['pcs','pack','bunch'].includes(item.unit) ? '1' : 'any'}
              value={row.amount} onChange={event => change(index, { amount: event.target.value })} />
            <p className="text-sm">Available: {item.quantity} {item.unit}{row.amount !== '' && Number(row.amount) <= item.quantity && Number(row.amount) >= 0 ? ` · Remaining: ${Number((item.quantity - Number(row.amount)).toPrecision(12))} ${item.unit}` : ''}</p>
          </>}
      </div>;
    })}
    {validation && <p className="alert-error" role="alert">{validation}</p>}
    <div className="flex flex-wrap gap-3">
      <button className="btn-primary" disabled={busy} type="submit">Confirm cooking and update fridge</button>
      <button className="btn-secondary" disabled={busy} type="button" onClick={onCancel}>Cancel cooking</button>
    </div>
  </form>;
}
