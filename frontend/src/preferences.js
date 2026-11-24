// Keep the API's exact ordered list values reversible in the editable fields.
export function formatPreferences(values) {
  return values
    .map((value) => {
      if (value.trim() === value && !/[",\r\n]/.test(value)) return value;
      return `"${value.replaceAll('"', '""')}"`;
    })
    .join(", ");
}

function skipSpace(text, index) {
  while (index < text.length && text[index].trim() === "") index++;
  return index;
}

function quotedEntry(text, start) {
  let value = "",
    index = start + 1;
  while (index < text.length) {
    const end = text.indexOf('"', index);
    if (end < 0) break;
    value += text.slice(index, end);
    if (text[end + 1] !== '"') return { value, end: end + 1 };
    value += '"';
    index = end + 2;
  }
  throw new Error(
    "Close every quoted entry. Use two double quotes for a quote inside a name.",
  );
}

function readEntry(text, start) {
  const index = skipSpace(text, start);
  if (text[index] === '"') {
    const entry = quotedEntry(text, index);
    const end = skipSpace(text, entry.end);
    if (end < text.length && text[end] !== ",")
      throw new Error("Separate quoted entries with commas.");
    if (!entry.value.trim())
      throw new Error("A quoted entry must contain a name.");
    return { value: entry.value, end };
  }
  const comma = text.indexOf(",", index);
  const end = comma < 0 ? text.length : comma;
  const value = text.slice(index, end).trim();
  if (value.includes('"'))
    throw new Error(
      "Put a name containing quotes in a quoted entry; double each quote inside it.",
    );
  return { value, end };
}

export function parsePreferences(text) {
  const values = [];
  let index = 0;
  while (index < text.length) {
    const entry = readEntry(text, index);
    if (entry.value) values.push(entry.value);
    index = entry.end + 1;
  }
  return values;
}
