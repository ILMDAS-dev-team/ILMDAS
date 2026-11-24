export default function SignInPage() {
  return (
    <section>
      <h1>Sign in</h1>
      <p>Please enter your credentials to access the staff workspace.</p>
      <form method="post" action="/api/v1/auth/login/">
        <div>
          <label htmlFor="username">Username</label>
          <input id="username" name="username" type="text" required />
        </div>
        <div>
          <label htmlFor="password">Password</label>
          <input id="password" name="password" type="password" required />
        </div>
        <button type="submit">Sign in</button>
      </form>
    </section>
  )
}
