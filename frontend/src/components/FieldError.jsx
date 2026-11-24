export default function FieldError({ id, children }) {
  return children ? (
    <p id={id} className="field-error" role="alert">
      {children}
    </p>
  ) : null;
}
