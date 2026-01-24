Context: Major Frontend Overhaul. We are moving from a simple Login to a "Multi-Portal Funnel".
Tech Stack: React, Tailwind, Lucide Icons. (Assume Shadcn/UI style).

## The Mission: Build the "Moxi Portal" Experience

### STEP 1: The Landing Page ("The Lobby")
Create a new component `src/pages/Landing.tsx`.
* **Design:** High-end, clean Vercel-style aesthetics.
* **Content:** 3 Distinct Entry Cards (Portals):
    1.  **Borrowers:** "I need a loan." (CTA: "Get Started")
    2.  **Staff:** "I work here." (CTA: "Staff Login")
    3.  **Partners:** (Infer from SOP, default to "Real Estate Partners").
* **Action:** Clicking "Borrowers" routes to `/funnel`.

### STEP 2: The Borrower Funnel ("The Hook")
Create `src/pages/BorrowerFunnel.tsx`.
* **Mechanism:** A multi-step "Wizard" (Click-Click-Click). No typing, just buttons.
* **Step 1 (Purpose):** Buttons: "Buy a Home" | "Refinance".
* **Step 2 (Occupancy):** Buttons: "Primary Residence" | "Vacation Home" | "Investment".
* **Step 3 (Credit):** Buttons: "Excellent (>720)" | "Good (680-720)" | "Fair (<680)".
* **Step 4 (Registration):** The final step is the "Create Account" form.
* **Logic:** Store answers in React State. When they Register, send this data as `initial_metadata` to the Registration API.

### STEP 3: API Integration (Update Auth)
Update `src/services/auth.ts` and `backend/app/api/routes/auth.py`.
* **Requirement:** The Registration endpoint must accept `initial_metadata` (the funnel answers) and save it to the User's profile or creates a draft Application immediately.

### STEP 4: The Dashboard (Document Upload)
* **Logic:** Once logged in, if the user has `initial_metadata` but no uploaded docs, show the "Document Upload" interface (the existing code you built).
* **Refinement:** Style this to look like a "Task List" rather than just a raw form.

## Execution
Generate the code for `Landing.tsx`, `BorrowerFunnel.tsx`, and the updated `auth.ts`.
Focus on "Vercel-like" UI: use generous padding, clean typography (Inter font), and subtle borders.