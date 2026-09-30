# Research-led AI leader site design

## Outcome

The site will position Berkcan Kapusuzoglu for senior AI research and technical-leadership roles. It will show a consistent path from scientific machine learning and uncertainty quantification to current work in language-model post-training, reasoning, model efficiency, evaluation, and scalable deployment.

The site will remain a static Hugo site hosted on GitHub Pages. The redesign will replace the legacy Wowchemy rendering stack with a small local template system that Berkcan can understand and maintain.

## Positioning

The primary message is:

> I lead research and engineering for efficient, reliable language models.

The supporting copy will identify Berkcan as a Staff Applied Researcher working across post-training, model efficiency, evaluation, and large-scale distributed systems. It will emphasize the ability to move from a research question to a validated method and then to a production-quality system.

The site will claim technical leadership, not people management. Leadership evidence will include research direction, technical ownership, model-release standards, cross-team adoption, and mentoring only where the source material supports those claims.

## Audience and success criteria

The primary audience is hiring leaders and senior researchers evaluating candidates for staff, principal, and research-lead roles in applied AI.

The redesign succeeds when a visitor can answer these questions within one minute:

1. What problems does Berkcan lead?
2. What is distinctive about his work?
3. What research and systems prove the claim?
4. How can the visitor read the work or contact him?

The owner succeeds when he can update biography text, featured work, publications, and research notes by editing documented Markdown or YAML files.

## Information architecture

### Home

The homepage will contain:

1. A single positioning-focused H1 and short supporting statement.
2. Links to selected research, CV, Google Scholar, GitHub, LinkedIn, and email.
3. A compact proof section using only public or employer-approved facts.
4. Three areas of focus: reasoning and distillation, efficient model architectures, and scalable and reliable ML systems.
5. Three featured research items in this order:
   1. Critique-Guided Distillation for Robust Reasoning via Refinement.
   2. When Load-Balancing Goes Too Far: Expert Pruning in Over-Dispersed Mixture-of-Experts Models.
   3. SPEAR-MM: Selective Parameter Evaluation and Restoration via Model Merging for Efficient Financial LLM Adaptation.
6. A concise career arc from scientific ML to frontier LLM research and production systems.
7. A direct contact call to action.

The current long biography and sparse News section will not remain on the homepage.

### Research

Research pages will organize work into three themes:

- Efficient reasoning and post-training.
- Model compression and scalable training.
- Trustworthy ML, evaluation, and uncertainty.

Each theme will explain the problem, Berkcan's contribution, selected evidence, and related publications. Private implementation details and unapproved employer-sensitive metrics will not be published.

### Publications

The publications page will contain an annotated selected-work section followed by the complete bibliography. Every item will show authors, title, year, exact venue and status, and descriptive links such as Paper, PDF, DOI, Code, or Slides.

Publication records will distinguish main-conference papers, workshop papers, accepted papers, published proceedings, preprints, and work under review. The design will not describe workshop papers as main-track conference papers.

The publication data model will use structured fields for title, date, slug, authors, venue name and type, DOI, links, topics, featured state, summary, and contribution. The rendering template will highlight Berkcan's name rather than storing Markdown inside author data.

### Leadership

The leadership page will present technical ownership, research direction, scalable training and evaluation systems, model-release standards, and cross-team adoption. It will avoid confidential business-unit names, private benchmarks, the résumé's phone number and ZIP code, and unapproved internal system details.

### About

The About page will contain a concise biography, corrected education history, professional links, CV download, and contact information. It will use the official current title, Staff Applied Researcher - AI Foundations.

### Research notes

The existing News section will be removed. A Research Notes section will be included only when substantive material is ready. Initial topics are critique-guided distillation, MoE load balancing and pruning, adaptive inference, enterprise model-release gates, and lessons carried from physics-informed ML into LLM research.

## Content and claim policy

Paper-backed results are preferred. Internal metrics will appear only after Berkcan confirms they are public or employer-approved.

The site will avoid unsupported absolutes such as "zero performance loss" and "zero regression." Where such claims are retained, they will name the evaluation scope, for example "no measured regression on the internal evaluation suite."

All venue labels will be verified against primary sources before publication. Submitted work will appear under Preprints or Under Review rather than the peer-reviewed section.

The following inconsistencies will be resolved against canonical sources:

- Current job title and AI Foundations start date.
- Delft and Erlangen-Nuremberg degree mappings.
- Unknown or malformed venue names.
- Duplicate publication records.
- Author-list and publication-year disagreements.

## Technical architecture

Hugo and GitHub Pages will remain. The active Wowchemy theme, dormant Netlify CMS integration, and publication-import submodule will be removed after their replacements are working.

The target rendering layer will contain local Hugo templates for the base page, homepage, lists, individual pages, publications, header, footer, and SEO metadata. Styling will use one local CSS entry point and minimal JavaScript.

Content will live in Markdown page bundles. Shared identity and proof-point data will live in a small profile data file. Existing public URLs will remain valid during the migration; URL-format changes are out of scope for the redesign.

The deployment workflow will separate read-only pull-request builds from production deployment permissions. Publication importing will not run during site deployment. Any future bulk importer should create a reviewable draft pull request.

## Accessibility and discoverability

Every page will have one meaningful H1, semantic landmarks, a skip link, visible keyboard focus, accessible social links, and useful image alternative text. Motion will respect reduced-motion preferences. The design will be reviewed at mobile and desktop widths.

The homepage will include useful title and description metadata plus Person structured data. Complete publication records will expose ScholarlyArticle metadata. Empty galleries, thin taxonomy pages, and generic metadata will not be indexed.

## Visual direction

The visual system will feel like a research leader's working portfolio rather than an academic template or a corporate landing page. Typography will provide the primary identity. The design will use a restrained technical palette, strong editorial hierarchy, generous reading width, and one distinctive visual device derived from model routing or research diagrams.

Decorative cards, generic gradients, excessive animation, and unexplained metrics will be avoided. The site will support light and dark presentation only if both can be maintained to the same standard.

## Validation

Pull requests will:

- Build with the same pinned Hugo version used in production.
- Treat warnings and path warnings as failures.
- Check internal links and assets.
- Assert one meaningful H1 per page.
- Validate required publication fields and reject placeholder venues, duplicate slugs, and truncated summaries.
- Run accessibility smoke tests on Home, Research, Publications, one publication, Leadership, and About at mobile and desktop widths.
- Check keyboard navigation, console errors, the CV link, sitemap, robots file, canonical URLs, social metadata, and the 404 page.

External-link checks will run separately or on a schedule so third-party outages do not block ordinary pull requests.

## Owner workflow

The README will document these tasks:

1. Preview the site locally with the pinned Hugo version.
2. Edit biography, research, and leadership copy.
3. Add a publication from an archetype.
4. Mark and reorder featured research.
5. Add a research note.
6. Replace the CV.
7. Open a pull request, review checks, merge, and confirm deployment.

## Migration sequence

1. Stabilize deployment, remove unused CMS output from builds, and capture the current URL set.
2. Create the local semantic site shell and accessibility foundations.
3. Migrate the homepage, Research, Publications, Leadership, About, and optional Research Notes content.
4. Normalize publication records and add verified 2025-2026 work.
5. Remove legacy themes, copied overrides, obsolete scripts, the Scholar submodule, and unused content.
6. Add automated validation and finish the owner README.

## Out of scope

- A database or server-side application.
- A headless CMS.
- Automatic publication changes that bypass review.
- Publishing confidential employer data.
- Frequent generic AI news posts.
- Changing the public domain or intentionally breaking existing URLs.
