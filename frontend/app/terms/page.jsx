import LegalPage from "@/components/LegalPage";

export const metadata = { title: "Terms of service" };

const CONTACT = "ashutoshabhinavbachra0009@gmail.com";

export default function TermsPage() {
  return (
    <LegalPage title="Terms of service" updated="9 November 2026">
      <p>
        These terms cover your use of ContractIQ, a contract review and e-signature tool built by Abhinav Ashutosh. By
        creating an account or signing a document, you agree to them.
      </p>

      <h2>Not legal advice</h2>
      <p>
        ContractIQ uses AI to point out clauses, risks and deadlines worth reviewing. It can miss things or get them
        wrong. It is not a lawyer and does not give legal advice. For anything important, have a qualified lawyer
        review the contract.
      </p>

      <h2>E-signatures</h2>
      <p>
        Signatures made in ContractIQ are simple electronic signatures with an audit trail (who signed, when, from
        which IP address and browser, and a fingerprint of the exact file). They are not Aadhaar eSign or a digital
        signature certificate. Whether a simple electronic signature is enough for a particular document depends on
        the law that applies to it; check before relying on it.
      </p>

      <h2>Your account and content</h2>
      <ul>
        <li>Keep your sign-in details safe; you are responsible for what happens in your account.</li>
        <li>You keep ownership of the contracts you upload. You give us permission to store and process them only to run the service for you.</li>
        <li>Only upload documents you have the right to share, and only send signing requests to people who expect them.</li>
      </ul>

      <h2>Acceptable use</h2>
      <p>
        Don&rsquo;t use ContractIQ to send spam, to impersonate anyone, to break the law, or to try to get into other
        people&rsquo;s accounts or data. We may suspend accounts that do.
      </p>

      <h2>The service</h2>
      <p>
        ContractIQ is provided free and &ldquo;as is&rdquo;, without any guarantee that it will always be available or
        error-free. Features may change. Keep your own copies of important documents. To the extent the law allows,
        we are not liable for losses that come from using it.
      </p>

      <h2>Ending your use</h2>
      <p>
        You can stop using ContractIQ at any time and ask us to delete your account. See the{" "}
        <a href="/privacy" className="text-pen underline">
          privacy policy
        </a>{" "}
        for what we store and how to have it removed.
      </p>

      <h2>Contact</h2>
      <p>
        <a href={`mailto:${CONTACT}`} className="text-pen underline">{CONTACT}</a>. If these terms change, the date at the top changes too.
      </p>
    </LegalPage>
  );
}
