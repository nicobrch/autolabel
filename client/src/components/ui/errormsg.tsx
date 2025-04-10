export function ErrorMessage({ error }: { error: string }) {
  return <div className="bg-red-50 text-red-500 p-3 rounded mb-4">{error}</div>;
}
