GAATHA MASTER PROJECT

Master Source of Truth

Date: 21 September 2026
Projects in scope: Gaatha Suite, Gaatha POS, Sentira, PostPilot
Markets: India + Albania / Europe
Architecture principle: Existing products first, controlled integration second

---

1. PURPOSE

This document is the master planning document for the four existing Gaatha projects:

1. Gaatha Suite
2. Gaatha POS
3. Sentira
4. PostPilot

The purpose is to create a coordinated Gaatha product ecosystem without blindly merging the four repositories.

The existing applications should first be:

- inspected
- stabilized
- documented
- secured
- standardized where appropriate
- connected through defined interfaces
- tested
- progressively commercialized

The master project must preserve the working capabilities of each application.

---

2. PROJECTS IN SCOPE

2.1 Gaatha Suite

Repository:

"gaathasuite/gaathasuite-main"

The repository contains a substantial business-suite / ERP implementation.

The tree shows:

- Backend
- Frontend
- PostgreSQL-related infrastructure
- Docker
- Production Docker Compose
- Nginx deployment configuration
- Migrations
- Tests
- Kubernetes configuration
- Render deployment configuration
- Operations scripts
- Backup/restore tooling
- Security documentation
- Multi-tenancy documentation
- ERP completion documentation

Important application areas visible in the repository include:

- Accounting
- CRM
- Sales
- Quotations
- Invoices
- Expenses
- Purchasing
- Inventory
- Vendors
- HR
- Approvals
- Reports
- Business Intelligence
- Multi-tenancy
- Authentication / authorization

The exact current implementation status must be determined from the repository itself before making further architecture decisions.

---

3. GAATHA POS

Repository:

"gaathapos/gaathapos-main"

The tree shows a Flask-based POS application with:

- Admin
- Analytics
- API
- Authentication
- Inventory
- KDS
- Menu
- Payments
- POS
- Multi-tenant launch documentation
- Docker
- PostgreSQL-related configuration
- Celery
- Migrations
- Smoke tests
- Tenant-isolation tests
- Payment-integrity tests
- Security tests
- Checkout-flow tests
- Inventory-integrity tests

Relevant application files include:

"app.py"

"config.py"

"models.py"

"routes.py"

"services/"

"blueprints/"

"migrations/"

"tests/"

The repository also contains deployment and beta-launch documentation.

Gaatha POS should remain a specialized operational application rather than being unnecessarily absorbed into Gaatha Suite.

---

4. SENTIRA

Repository:

"sentira/sentira-main"

The tree shows a substantially larger AI/CCTV platform.

Major application components include:

- "apps/ai-worker"
- "apps/api"
- "apps/edge-connector"
- "apps/stream-gateway"
- "apps/web"

The repository also contains documentation for:

- AI pipeline
- AI worker
- Analytics
- API
- Architecture
- CCTV architecture
- CCTV knowledge base
- CCTV support
- Database
- Demo
- Deployment
- Disaster recovery
- Legal compliance
- Observability
- RBAC
- Retention
- Rule engine
- Streaming
- Video pipeline
- VPS deployment
- CCTV onboarding
- Hardware testing
- Performance
- Tracking
- WebRTC

The repository contains production Docker configuration and Nginx deployment configuration.

Sentira is therefore treated as the Gaatha ecosystem's physical-world visual intelligence application.

It should remain independently deployable.

---

5. POSTPILOT

Repository:

"postpilot/postpilot-main"

The tree shows a Flask/Python-based automation application with functionality around:

- Facebook
- Instagram
- YouTube
- RSS/news
- Content posting
- Content automation
- Video generation
- Uploading
- Scheduled/automated workflows

Important files include:

- "app.py"
- "facebook_api.py"
- "fetch_fb_info.py"
- "fetch_full_info.py"
- "gaatha_loop.py"
- "grahak_news_auto.py"
- "grahak_uploader.py"
- "grahak_video_factory.py"
- "grahak_youtube_auto.py"
- "grahakchetna.py"
- "insta.py"
- "posting_utils.py"

The repository also contains:

- Docker configuration
- SQLite database
- deployment scripts
- smoke tests
- environment template
- social/content configuration files

PostPilot should initially remain a separate application and be integrated only where a clearly useful business/marketing connection exists.

---

6. MASTER ECOSYSTEM

The four applications should be viewed as one ecosystem but four independently maintained products.

                    GAATHA ECOSYSTEM
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
 GAATHA SUITE         GAATHA POS          SENTIRA
 Business Suite       Food/POS            CCTV/AI
        |                  |                  |
        +------------------+------------------+
                           |
                    Business / Operations
                           |
                           v
                       POSTPILOT
                  Marketing / Automation

This diagram represents an integration direction.

It does not mean that the applications should immediately share databases or be merged into one codebase.

---

7. MASTER ARCHITECTURE PRINCIPLE

Do not merge repositories blindly.

Each application has its own:

- architecture
- database
- deployment model
- dependencies
- authentication
- configuration
- operational requirements

The master project should introduce integration gradually.

---

8. DATABASE STRATEGY

The initial architecture should use separate databases.

Conceptually:

Gaatha Suite DB
Gaatha POS DB
Sentira DB
PostPilot DB

Do not create a single shared database merely to make integration easier.

Cross-product data should eventually move through controlled:

- APIs
- integration services
- events
- webhooks
- documented data contracts

Direct access to another application's private tables should be avoided unless explicitly designed and justified.

---

9. IDENTITY AND TENANCY

Gaatha Suite and Gaatha POS already contain multi-tenancy-related implementation/documentation.

Sentira also contains RBAC/security architecture.

The first task is therefore not to replace all authentication systems.

Instead:

1. Inspect the existing identity models.
2. Inspect tenant models.
3. Inspect roles and permissions.
4. Identify conflicts.
5. Identify common concepts.
6. Design an integration strategy.
7. Preserve backward compatibility.

A future unified identity experience may be possible, but it should only be implemented after the existing systems are understood.

---

10. SHARED SERVICES

Potential shared services may include:

- Email
- Notifications
- Organization information
- User identity
- Authentication
- Billing
- Audit conventions
- Application registration
- Integration events

However, these are future integration targets, not assumptions that they already exist as shared services.

---

11. ENVIRONMENT AND SECRET STRATEGY

The user intends to provide required credentials such as:

- Groq API key
- Gmail application credentials
- Other required environment variables

These credentials must never be placed inside:

- source code
- Git commits
- this master document
- Copilot prompts
- public documentation

Use environment variables and secure deployment configuration.

---

12. ENVIRONMENT INVENTORY

Before deciding which environment variables can be shared, inspect all four applications.

For each variable document:

Field| Required
Variable name| Yes
Application| Yes
File where consumed| Yes
Purpose| Yes
Required/optional| Yes
Secret/non-secret| Yes
Shared candidate| Yes
Application-specific| Yes
Production requirement| Yes
Development requirement| Yes

Do not assume that two variables with similar names have the same meaning.

---

13. EMAIL

Gmail / SMTP can potentially become a common infrastructure service.

However:

- credentials remain secret
- each application must be inspected
- existing email functionality must be preserved
- configuration names should only be standardized after confirming usage

The first phase should identify all existing email implementations.

---

14. AI PROVIDER

If Groq is required by one or more applications, document:

- where the key is consumed
- which model is used
- which application uses it
- whether the integration is production-ready
- whether another application has an independent AI configuration

Do not automatically force all applications to use one AI abstraction.

---

15. INTEGRATION MODEL

The preferred long-term model is:

Application A
     |
     | API / Event
     v
Integration Boundary
     |
     v
Application B

rather than:

Application A
     |
     | direct SQL
     v
Application B database

This keeps applications independently maintainable.

---

16. POTENTIAL GAATHA SUITE ↔ GAATHA POS CONNECTION

Gaatha Suite and Gaatha POS have the most obvious business-system relationship.

Potential integration areas include:

Gaatha Suite
    |
    +-- Inventory
    +-- Purchasing
    +-- Vendors
    +-- Accounting
    +-- Expenses
    +-- Reporting
    |
    v
Gaatha POS
    |
    +-- Menu
    +-- Orders
    +-- Tables
    +-- KDS
    +-- Payments
    +-- Restaurant operations

The exact integration contract must be created only after inspecting the actual models and APIs in both repositories.

---

17. POTENTIAL SENTIRA ↔ GAATHA POS CONNECTION

Sentira can potentially generate operational events relevant to food/restaurant environments.

Example:

Camera
   ↓
Sentira detection
   ↓
Configured rule
   ↓
Operational event
   ↓
POS / business workflow
   ↓
Notification
   ↓
Resolution

Possible examples should only be implemented where supported by actual Sentira capabilities and the business requirements.

The master project must not invent undocumented Sentira detections.

---

18. POTENTIAL SENTIRA ↔ GAATHA SUITE CONNECTION

Sentira events could eventually become business/operational events inside Gaatha Suite.

Potential categories:

- Incident
- Operational alert
- Facility observation
- Staff-related workflow
- Asset/facility event

Again, exact event types must be determined from the Sentira implementation and business requirements.

---

19. POSTPILOT INTEGRATION

PostPilot is different from the other three applications.

Its primary integration opportunity is around:

- Marketing
- Content
- Social publishing
- Business communication
- Promotional workflows

Potential future direction:

Gaatha Suite
     |
     | approved marketing/content data
     v
PostPilot
     |
     +--> Facebook
     +--> Instagram
     +--> YouTube
     +--> Other configured channels

This should be implemented only through controlled APIs/data exchange.

---

20. MASTER IMPLEMENTATION PHASES

PHASE 0 — REPOSITORY INVENTORY

First inspect all four repositories.

Goal

Understand exactly what currently exists.

Inspect:

- Application structure
- Backend
- Frontend
- Database
- Migrations
- Authentication
- RBAC
- Tenant isolation
- APIs
- Environment variables
- Docker
- Docker Compose
- Deployment
- Nginx
- Storage
- Redis
- Celery/background workers
- External services
- Tests
- Existing documentation

Deliverable

docs/ENVIRONMENT_AND_INTEGRATION_INVENTORY.md

---

21. PHASE 1 — ARCHITECTURE COMPATIBILITY

Compare the four applications.

Document:

- Technology stack
- Authentication
- Tenant model
- User model
- Organization model
- Database model
- API structure
- Configuration
- Deployment
- Logging
- Audit
- Notifications
- External integrations

Identify:

Compatible

Things that can be standardized.

Independent

Things that should remain application-specific.

Conflicting

Things that require an explicit architecture decision.

---

22. PHASE 2 — SECURITY FOUNDATION

Before cross-product integration:

- Review secrets
- Review environment configuration
- Review tenant isolation
- Review RBAC
- Review authentication
- Review API authorization
- Review public ports
- Review Docker networking
- Review database exposure
- Review storage access
- Review production configuration

No integration should weaken an existing security boundary.

---

23. PHASE 3 — COMMON INTEGRATION CONTRACT

Create a documented contract for:

- Application identity
- Organization identity
- User identity
- Tenant identity
- API authentication
- Event naming
- Event payloads
- IDs
- Error handling
- Webhooks
- Integration logging

This becomes the foundation for connecting the four products.

---

24. PHASE 4 — GAATHA SUITE ↔ GAATHA POS

Start with the most obvious operational/business connection.

Potential areas:

1. Inventory
2. Purchasing
3. Vendors
4. Sales
5. Accounting
6. Reporting

Do not implement every integration simultaneously.

Begin with one controlled end-to-end workflow.

---

25. PHASE 5 — SENTIRA INTEGRATION

Connect Sentira to business workflows through controlled events.

Start with a narrow, measurable use case.

Validate:

- Event creation
- Authentication
- Tenant ownership
- Event delivery
- Failure handling
- Duplicate handling
- Auditability

---

26. PHASE 6 — POSTPILOT INTEGRATION

After the business applications are stable:

- Identify useful Suite → PostPilot data
- Define marketing/content API
- Define approval flow
- Define publishing status
- Define error handling
- Keep social credentials isolated

---

27. PHASE 7 — UNIFIED CUSTOMER EXPERIENCE

Only after the underlying systems are stable should we consider:

- Common login
- Unified organization selection
- Cross-product navigation
- Shared account management
- Unified subscription/billing
- Unified notifications

This should be treated as a later platform layer.

---

28. PHASE 8 — COMMERCIALIZATION

The four products can eventually be positioned as connected products.

Gaatha Suite

Business management.

Gaatha POS

Restaurant / food operations.

Sentira

AI/CCTV operational intelligence.

PostPilot

Marketing/content automation.

The commercial strategy can offer products independently while allowing customers to connect multiple products when useful.

---

29. FIRST MASTER ENGINEERING TASK

The first task is NOT:

- Merge repositories
- Rewrite authentication
- Create a shared database
- Change production deployments
- Replace existing architectures
- Modify migrations unnecessarily

The first task is:

«Create a factual inventory of the four repositories.»

---

30. FIRST DOCUMENT

Create:

docs/ENVIRONMENT_AND_INTEGRATION_INVENTORY.md

It must contain:

A. Project inventory

- Gaatha Suite
- Gaatha POS
- Sentira
- PostPilot

B. Technology inventory

For each project:

- Backend
- Frontend
- Database
- Cache
- Workers
- Storage
- APIs
- Deployment

C. Environment inventory

Every environment variable.

D. Integration inventory

Every external service/API.

E. Security inventory

- Authentication
- Authorization
- RBAC
- Tenant isolation
- Secrets
- Public exposure

F. Database inventory

- Database type
- Migration system
- Current migration structure
- Major models
- Tenant relationships

G. Deployment inventory

- Docker
- Compose
- Nginx
- Ports
- Domains if documented
- Health checks
- Production services

H. Testing inventory

- Unit tests
- Integration tests
- Smoke tests
- Security tests
- E2E tests

I. Existing documentation

Record important existing documentation rather than duplicating it.

J. Conflicts

Document conflicts between projects.

K. Integration opportunities

Document possible connections.

L. Integration risks

Document risks.

---

31. COPILOT WORKING RULES

All future Copilot prompts for this master project should follow these rules.

Inspect first.

Never assume architecture.

Implement within scope.

When implementation is requested, make the actual changes rather than only giving recommendations.

Avoid unnecessary rewrites.

Prefer targeted changes.

Preserve working functionality.

Do not remove working functionality without a clear reason.

Test changes.

Run appropriate tests after implementation.

Report exact results.

Example:

Tests:
52 passed
0 failed

No automatic commit/push.

Do not commit or push unless explicitly requested.

Never expose secrets.

Do not print environment secrets.

Production safety.

Do not restart or redeploy production unless specifically requested.

---

32. MASTER DIRECTORY

The master documentation should eventually look approximately like:

docs/
│
├── GAATHA_MASTER_PROJECT.md
├── ENVIRONMENT_AND_INTEGRATION_INVENTORY.md
├── INTEGRATION_ARCHITECTURE.md
├── SECURITY_INTEGRATION_PLAN.md
├── API_INTEGRATION_CONTRACT.md
├── EVENT_CONTRACT.md
└── MASTER_ROADMAP.md

These documents should be created progressively.

Do not create empty documentation just for the sake of structure.

---

33. MASTER DEVELOPMENT LOOP

Every phase follows:

INSPECT
   ↓
UNDERSTAND
   ↓
DOCUMENT
   ↓
DESIGN
   ↓
IMPLEMENT
   ↓
TEST
   ↓
VALIDATE
   ↓
DOCUMENT RESULT
   ↓
NEXT PHASE

---

34. MASTER PROJECT RULE

«Do not build a new ecosystem by destroying the existing applications.

Build the ecosystem by making the existing applications reliable, compatible and progressively connected.»

---

35. CURRENT MASTER STATUS

As of:

21 September 2026

In scope

- [x] Gaatha Suite
- [x] Gaatha POS
- [x] Sentira
- [x] PostPilot

Explicitly NOT in scope

- [ ] Phoenix
- [ ] Gaatha AI
- [ ] Any other application not present in the supplied repository tree

Current phase

PHASE 0 — Repository / Environment / Integration Inventory

Immediate deliverable

docs/ENVIRONMENT_AND_INTEGRATION_INVENTORY.md

Next decision

Do not begin cross-product code integration until the inventory has been reviewed.

---

36. MASTER PROJECT OBJECTIVE

The objective is to create a reliable, commercially usable and progressively integrated Gaatha ecosystem consisting of:

                    GAATHA ECOSYSTEM
                           |
       +-------------------+-------------------+
       |                   |                   |
       v                   v                   v
 GAATHA SUITE        GAATHA POS             SENTIRA
 Business ERP        Food / POS          CCTV / AI
       |                   |                   |
       +-------------------+-------------------+
                           |
                           v
                      POSTPILOT
                 Marketing Automation

Each product remains valuable independently.

The ecosystem creates additional value when products are connected.

---

37. FINAL MASTER RULE

Four repositories.

Four products.

One coordinated roadmap.

No unnecessary merging.

No invented architecture.

No undocumented assumptions.

Inspect → implement → test → validate → integrate.