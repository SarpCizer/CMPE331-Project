/** Unimplemented acceptance boundary; no production behavior is provided. */
export async function createAcceptanceApp({ recipeProvider, clock } = {}) {
  return {
    async request({ method, path, token, body }) {
      return { status: 501, body: { error: 'Feature not implemented', method, path } };
    },
    async close() {},
  };
}
