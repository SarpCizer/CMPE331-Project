import FieldError from './FieldError';

export function amountInput(quantity, unit, required = false) {
  if (quantity.trim() === '' && !required) return { body: {}, error: '' };
  const amount = Number(quantity);
  if (quantity.trim() === '' || !Number.isFinite(amount) || amount <= 0 || amount > 1000000 ||
      (['pcs', 'pack', 'bunch'].includes(unit) && !Number.isInteger(amount))) {
    return { body: {}, error: 'Enter a positive quantity up to 1,000,000; use whole numbers for pcs, pack and bunch.' };
  }
  return { body: { quantity: amount, unit }, error: '' };
}

export default function ShoppingAmount({ id, quantity, unit, setQuantity, setUnit, error, disabled = false, required = false }) {
  return <>
    <div className="w-[120px] mobile:flex-1">
      <label htmlFor={`${id}-quantity`} className="text-[0.8rem]">{required ? 'Bought quantity' : 'Quantity (optional)'}</label>
      <input id={`${id}-quantity`} type="number" min="0.000001" max="1000000" step="any"
        value={quantity} disabled={disabled} required={required}
        onChange={event => setQuantity(event.target.value)} aria-invalid={!!error}
        aria-describedby={error ? `${id}-quantity-error` : undefined} />
      <FieldError id={`${id}-quantity-error`}>{error}</FieldError>
    </div>
    <div className="w-[105px] mobile:flex-1">
      <label htmlFor={`${id}-unit`} className="text-[0.8rem]">Unit</label>
      <select id={`${id}-unit`} disabled={disabled} value={unit} onChange={event => setUnit(event.target.value)}
        className="w-full rounded-lg border border-line bg-white p-2">
        {['pcs', 'kg', 'g', 'L', 'ml', 'pack', 'bunch'].map(value => <option key={value} value={value}>{value}</option>)}
      </select>
    </div>
  </>;
}
