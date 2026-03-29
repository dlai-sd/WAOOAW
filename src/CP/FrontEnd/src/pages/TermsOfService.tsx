import Footer from '../components/Footer'

export default function TermsOfService() {
  return (
    <main className="legal-page" data-testid="legal-terms-page">
      <section className="legal-hero">
        <div className="container legal-hero-content">
          <div className="legal-kicker">Terms of Service</div>
          <h1>Rules for using WAOOAW</h1>
          <p>
            These terms explain the conditions for accessing WAOOAW, starting trials, hiring agents, and using
            connected-platform workflows through the service.
          </p>
          <div className="legal-meta">Last updated: March 29, 2026</div>
        </div>
      </section>

      <section className="legal-section">
        <div className="container legal-card-stack">
          <article className="legal-card">
            <h2>1. Acceptance of terms</h2>
            <p>
              By accessing or using WAOOAW, you agree to these Terms of Service and the Privacy Policy. If you do
              not agree, do not use the service.
            </p>
          </article>

          <article className="legal-card">
            <h2>2. Service description</h2>
            <p>
              WAOOAW is an AI agent marketplace that allows customers to discover agents, start trials, configure
              workflows, review outputs, and in some cases connect third-party platforms to support approved tasks.
            </p>
          </article>

          <article className="legal-card">
            <h2>3. Eligibility and account responsibility</h2>
            <p>
              You are responsible for ensuring that the information you provide is accurate and that your account,
              devices, and access methods are kept secure. You are also responsible for activity that occurs under
              your account unless caused by WAOOAW systems or staff.
            </p>
          </article>

          <article className="legal-card">
            <h2>4. Trials, subscriptions, and billing</h2>
            <p>
              WAOOAW may offer free trials, paid subscriptions, usage-based features, or promotional offers. Trial,
              billing, renewal, cancellation, and refund terms may vary by product or plan and will be shown at the
              point of purchase or activation.
            </p>
            <p>
              Unless expressly stated otherwise, fees that become due are your responsibility and must be paid under
              the applicable plan terms.
            </p>
          </article>

          <article className="legal-card">
            <h2>5. Customer content and permissions</h2>
            <p>
              You retain responsibility for the content, data, media, prompts, business instructions, and external
              accounts you provide to WAOOAW. You confirm that you have the rights and permissions needed to use
              that content and to authorize any requested connected-platform actions.
            </p>
          </article>

          <article className="legal-card">
            <h2>6. Acceptable use</h2>
            <p>You may not use WAOOAW to:</p>
            <ul>
              <li>Break the law or violate third-party platform rules</li>
              <li>Upload, publish, or automate harmful, fraudulent, or infringing content</li>
              <li>Attempt unauthorized access to WAOOAW systems or another user’s data</li>
              <li>Interfere with platform stability, security, or other customers’ access</li>
              <li>Use connected-platform permissions for purposes outside the customer-approved workflow</li>
            </ul>
          </article>

          <article className="legal-card">
            <h2>7. Third-party services</h2>
            <p>
              WAOOAW may depend on third-party providers such as Google, payment providers, hosting services, and
              communications tools. Your use of connected services may also be subject to those providers’ terms and
              policies.
            </p>
          </article>

          <article className="legal-card">
            <h2>8. Intellectual property</h2>
            <p>
              WAOOAW and its platform materials, branding, software, and service design are protected by applicable
              intellectual property laws. Except where expressly granted, no license or ownership transfer is created
              by using the service.
            </p>
          </article>

          <article className="legal-card">
            <h2>9. Suspension and termination</h2>
            <p>
              We may suspend or terminate access if we reasonably believe there is fraud, abuse, legal risk,
              non-payment, security risk, or violation of these terms. You may stop using the service at any time,
              subject to any active billing commitments already incurred.
            </p>
          </article>

          <article className="legal-card">
            <h2>10. Disclaimers and limitation of liability</h2>
            <p>
              WAOOAW is provided on an "as is" and "as available" basis to the maximum extent permitted by law.
              We do not guarantee uninterrupted service, error-free outputs, or guaranteed business results.
            </p>
            <p>
              To the maximum extent permitted by law, WAOOAW will not be liable for indirect, incidental, special,
              consequential, or punitive damages arising from your use of the service.
            </p>
          </article>

          <article className="legal-card">
            <h2>11. Changes to terms</h2>
            <p>
              We may update these terms from time to time. Continued use of WAOOAW after updated terms take effect
              means you accept the revised version.
            </p>
          </article>

          <article className="legal-card">
            <h2>12. Contact</h2>
            <p>
              For questions about these terms, contact
              <a href="mailto:legal@waooaw.com"> legal@waooaw.com</a>.
            </p>
          </article>
        </div>
      </section>

      <Footer />
    </main>
  )
}