export default function ResourceError({ label, error, retry, busy }) {
  return (
    <section className="panel" role="alert">
      <h2>{label} could not be loaded</h2>
      <p className="wrap-anywhere">
        {error} Your saved data has not been replaced.
      </p>
      <button className="btn-secondary" disabled={busy} onClick={retry}>
        Retry {label.toLowerCase()}
      </button>
    </section>
  );
}
