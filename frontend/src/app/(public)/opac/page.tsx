type OpacPageProps = {
  searchParams: Promise<{ q?: string | string[]; category?: string | string[] }>
}

function first(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "")
}

export default async function OpacPage({ searchParams }: OpacPageProps) {
  const params = await searchParams
  const query = first(params.q).trim()
  const category = first(params.category).trim()

  return (
    <section className="simple-page">
      <h1>E-Book</h1>
      {query || category ? (
        <div className="search-summary" role="status">
          <p>
            Search request: <strong>{query || "All resources"}</strong>
            {category ? ` in ${category}` : ""}
          </p>
          <p>E-Book results will appear here when the E-Book index is published.</p>
        </div>
      ) : (
        <p>Use the search field on the homepage to look for library and archive resources.</p>
      )}
    </section>
  )
}
