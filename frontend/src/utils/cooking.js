// Convert compatible dimensions only. A cup of flour is not a cup of water.
export function cookingQuantity(measurement, stockUnit) {
  const match = String(measurement || '').trim().match(/^(\d+(?:\.\d+)?)\s*(kg|g|ml|L|pcs|pack|bunch)?$/);
  if (!match) return '';
  const amount = Number(match[1]);
  const source = match[2] || (stockUnit === 'pcs' ? 'pcs' : '');
  const units = { kg: ['mass', 1000], g: ['mass', 1], L: ['volume', 1000], ml: ['volume', 1],
    pcs: ['pcs', 1], pack: ['pack', 1], bunch: ['bunch', 1] };
  if (!units[source] || !units[stockUnit] || units[source][0] !== units[stockUnit][0]) return '';
  return String(Number((amount * units[source][1] / units[stockUnit][1]).toPrecision(12)));
}
