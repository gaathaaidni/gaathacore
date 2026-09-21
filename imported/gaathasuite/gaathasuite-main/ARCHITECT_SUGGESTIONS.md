## Gaatha Suite: Architectural & Development Suggestions (Audit-Based)

This document contains a running list of potential next steps, feature ideas, and architectural improvements for the Gaatha Suite project, based on our development sessions.
---
How can I add a feature to export the organizations table to a CSV file?
Can you add a confirmation modal before deactivating a coupon?
---
### Part 1: Product Readiness

*   **CRM**: Pending. No CRM module exists.
    *   "Design the database schema for a basic CRM with Accounts and Contacts."
    *   "Create the FastAPI routes for CRUD operations on CRM Accounts."
*   **HRMS**: In Progress.
    *   Employee records (CRUD) are implemented. (✓ Done)
    *   **Payroll**: Pending.
    *   **Attendance**: Pending.
    *   **Recruitment**: Pending.
*   **Accounting (Gaatha Books)**: Pending. No accounting module exists.
    *   "Design the database schema for Invoices and Customers."
*   **Inventory (Gaatha Inventory)**: Pending. No inventory module exists.
*   **Procurement (Sales/Purchase)**: Pending. No procurement modules exist.
*   **Project Management**: Pending. No project management module exists.
*   **Helpdesk**: Pending. No helpdesk module exists.
*   **Document Management**: Pending. No document management module exists.
*   **Workflow Automation**: Pending.
*   **Reporting & Dashboards**: Pending.
*   **Mobile Support**: Pending. The current frontend is not responsive.
*   **API Platform**: In Progress. Core API is FastAPI.
*   **AI Features**: In Progress. Vani chat assistant is implemented. (✓ Done)

---

### Part 2: Technical Architecture Review

*   **Backend Architecture**:
    *   Flask/FastAPI hybrid has been consolidated to pure FastAPI. (✓ Done)
    *   Asynchronous chat implemented with Celery. (✓ Done)
*   **Frontend Architecture**:
    *   React with Vite. (✓ Done)
    *   Real-time UI updates via WebSockets for AI alerts. (✓ Done)
    *   Background task polling UI implemented. (✓ Done)
*   **Database Design**:
    *   PostgreSQL with Alembic for migrations. (✓ Done)
    *   **Connection Pooling**: Pending. This is the highest priority technical task.
        *   "Show me how to configure SQLAlchemy with an AsyncPG connection pool."
*   **API Design**:
    *   RESTful principles applied in FastAPI routes. (✓ Done)
*   **Security**:
    *   **Authentication**: Session-based authentication via Flask-Login. (✓ Done)
    *   **Authorization**: Basic organization-level scoping is present. Role-Based Access Control (RBAC) is pending.
        *   "Design a database schema for Roles and Permissions."
        *   "Create a FastAPI dependency to check user roles for a specific route."
    *   **Audit Logging**: Pending.
    *   **Secrets Management**: Using environment variables and `.env` file. (✓ Done for dev)
*   **Scalability**:
    *   **WebSocket Scaling**: Implemented with Redis Pub/Sub. (✓ Done)
    *   **Background Jobs**: Implemented with Celery and Redis. (✓ Done)
*   **Performance**:
    *   **Caching**: Pending.
        *   "Show me how to implement a Redis cache for a FastAPI route."
    *   **Search**: Pending. No dedicated search functionality exists.

---

### Part 7: AI Competitiveness

*   **AI Capabilities**:
    *   Conversational AI (Vani) is implemented. (✓ Done)
    *   **Agentic Capabilities**: Pending. Vani cannot yet interact with other modules (i.e., "provision-workspace" tool is not implemented).
        *   "Write the Python code for a Vani tool that can create a new employee in the HR module."

---

### Part 9: Executive Action Plan (High-Priority Next Steps)

1.  **Database Connection Pooling**: Implement connection pooling to prepare the application for concurrent users. (Technical Debt)
    *   "Show me how to configure SQLAlchemy with an AsyncPG connection pool."
2.  **Build a Core Module**: Begin development of a core business module, such as the CRM. (Product Readiness)
    *   "Design the database schema for a basic CRM with Accounts and Contacts."
3.  **Implement RBAC**: Add Role-Based Access Control for more granular security. (Security)
    *   "Design a database schema for Roles and Permissions and connect them to Users."