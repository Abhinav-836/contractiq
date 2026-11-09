import LegalPage from "@/components/LegalPage";

export const metadata = { title: "Privacy policy" };

const CONTACT = "ashutoshabhinavbachra0009@gmail.com";

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy policy" updated="9 November 2026">
      <p>
        ContractIQ is a contract review and e-signature tool built by Abhinav Ashutosh. This page explains what we
        store, why, and what you can ask us to do with it. We don&rsquo;t sell your data or use it for advertising.
      </p>

      <h2>What we store</h2>
      <ul>
        <li>
          <strong>Your account:</strong> your name, email address and a hashed password (we never see the password
          itself).
        </li>
        <li>
          <strong>If you sign in with Google:</strong> only your name, email address and Google&rsquo;s account ID for
          you. We don&rsquo;t get your Google password, contacts, files or anything else from your Google account.
        </li>
        <li>
          <strong>Contracts you upload</strong> and what ContractIQ extracts from them: clauses, risks, obligations and
          deadlines.
        </li>
        <li>
          <strong>Signing records:</strong> when someone signs, we keep their name, email, the time, their IP address
          and browser, and a fingerprint (SHA-256) of the file they signed. This is the audit trail that proves who
          signed what.
        </li>
        <li>
          <strong>Workspace data:</strong> team members, invites, approvals and comments.
        </li>
        <li>
          <strong>Basic usage data:</strong> anonymous page-visit counts, so we know which features are used.
        </li>
      </ul>

      <h2>Why we use it</h2>
      <ul>
        <li>To sign you in and keep your contracts private to your account and workspace.</li>
        <li>To analyse the contracts you upload, which is what the product does.</li>
        <li>To send emails you asked for: approval and signing requests, signed copies, password resets.</li>
        <li>To keep a signing audit trail that holds up if a signature is disputed.</li>
      </ul>

      <h2>Who else handles it</h2>
      <p>We use a few services to run ContractIQ. Each one only gets what it needs:</p>
      <ul>
        <li>Render and Vercel host the app; the database is PostgreSQL on Render.</li>
        <li>An AI model provider receives the text of a contract when you ask for it to be analysed.</li>
        <li>Brevo sends the emails.</li>
        <li>Google handles &ldquo;Sign in with Google&rdquo; if you use it.</li>
      </ul>

      <h2>Your choices</h2>
      <ul>
        <li>You can delete contracts from your account at any time.</li>
        <li>
          You can ask us to delete your account and everything in it by emailing <a href={`mailto:${CONTACT}`} className="text-pen underline">{CONTACT}</a>. Signing records on contracts
          other people sent you may be kept, because they are those people&rsquo;s proof of signature.
        </li>
        <li>You can ask for a copy of the data we hold about you at the same address.</li>
      </ul>

      <h2>Security</h2>
      <p>
        Passwords are hashed, sign-in and signing links are stored only as hashes, and everything travels over HTTPS.
        No system is perfectly secure, so please don&rsquo;t upload documents you aren&rsquo;t allowed to share with
        a service like this.
      </p>

      <h2>Contact</h2>
      <p>
        Questions about privacy: <a href={`mailto:${CONTACT}`} className="text-pen underline">{CONTACT}</a>. If this policy changes, the date at the top changes too.
      </p>
    </LegalPage>
  );
}
