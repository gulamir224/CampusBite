# CampusBite — Design Thinking Project Report

**Project:** CampusBite — Smart College Canteen Management System  
**Tagline:** Skip the Queue, Enjoy Your Food!  
**Project type:** B.Tech Artificial Intelligence Design Thinking prototype

> **Research note:** This report turns the supplied project brief into a prototype and validation plan. No campus interviews or live canteen deployment were provided for this build, so user needs below are treated as hypotheses to verify rather than measured research findings.

## 1. Introduction

CampusBite is a student-first ordering experience for a college canteen. The prototype brings menu availability, ordering, pickup tokens, order tracking, and feedback into one responsive web application. Canteen staff receive a separate dashboard for managing the menu and order progress.

## 2. Problem identification

The design brief describes four connected problems: long canteen queues, short breaks lost while waiting, manual ordering during rush periods, and limited visibility into which foods are available. The problems affect students at the point of purchase and staff who must handle counter conversations, availability questions, payments, and preparation coordination at once.

### Opportunity

Let students check the menu and submit a pickup order before reaching the counter, then give both sides a clear order token and status.

## 3. Empathy mapping

| Student perspective | Prototype hypothesis |
|---|---|
| **Says** | “I only have a short break.” “Is this still available?” |
| **Thinks** | “I hope the queue is not long.” “Will my food be ready before class?” |
| **Does** | Checks the counter, asks what is available, waits, and pays in person. |
| **Feels** | Rushed when the break is short; uncertain when availability is unclear. |
| **Needs** | Quick menu discovery, trustworthy availability, a simple order confirmation, and pickup clarity. |

| Canteen staff perspective | Prototype hypothesis |
|---|---|
| **Says** | “What would you like?” “That item is sold out.” |
| **Thinks** | “I need a simple way to keep the menu current.” |
| **Does** | Takes orders, answers availability questions, prepares dishes, and calls customers. |
| **Feels** | Busy during peak breaks and interrupted by repeated status questions. |
| **Needs** | A manageable menu control, an order list, and clear preparation stages. |

These empathy maps are starting points. Interviews and observation at the target college should validate the wording and reveal other needs, including accessibility, dietary restrictions, pickup layout, and network availability.

## 4. User research

### Research questions for the next campus study

1. How long do students typically wait during breakfast and lunch breaks?
2. How often do students discover an item is unavailable only after reaching the counter?
3. What order and payment steps would students trust on their own phones?
4. How do staff currently communicate sold-out items and pickup readiness?
5. What would make students confident that a pre-order will be ready at the right time?

### Suggested method

- Interview 5–8 students across different years and break schedules.
- Interview 2–3 canteen staff members and observe one peak period with permission.
- Map the existing journey from deciding what to eat through receiving the food.
- Test the prototype with short tasks and record completion time, confusion, and missed actions.

### Evidence available in this prototype

The brief supplied for this build is the only source of user evidence so far. The project includes a local automated workflow suite for software behavior; those tests verify implementation, not real student usability.

## 5. Problem definition

**How might we help students order available canteen food before they arrive at the counter, so they spend more of a short break eating and less time queuing, while giving canteen staff a manageable way to update items and prepare orders?**

### Design principles

- Show availability before the student commits to an order.
- Keep the path from menu to checkout short and mobile-friendly.
- Make payment and pickup expectations explicit.
- Give staff a small set of clear, reversible controls.
- Never imply that a simulated payment transfers money.

## 6. Ideation

Ideas represented in the prototype include:

- Search and category filters for quick menu discovery.
- Availability indicators and admin-controlled sold-out states.
- A persistent cart and two pickup payment choices.
- A unique token with an estimated wait and four order stages.
- Rule-based recommendations using popularity, category, and a student's order history.
- A student feedback form connected to the admin view.

The rule-based recommendation approach was selected because the prototype has a small seeded menu and no verified training data. A paid model or trained machine learning system would add complexity without reliable evidence at this stage.

## 7. Proposed solution

CampusBite uses a Flask web application, Jinja templates, and SQLite. Students can register, browse the menu, build a persistent cart, place a cash-on-pickup or demo-UPI order, receive a token, and track its status. Staff can sign in separately to manage dishes, availability, prices, orders, and feedback.

The UPI flow is deliberately simulated. Its payment page labels the QR visual as non-scannable, and completing it creates a demo transaction reference only. No gateway or actual money movement is involved.

## 8. Prototype development

### Main prototype components

- Flask app factory and session-based student/admin access.
- SQLite tables for users, admins, food items, cart, orders, order items, payments, and feedback.
- Responsive home, menu, cart, checkout, token, tracking, profile, feedback, and admin pages.
- Seeded menu items priced in INR.
- Password hashing, form CSRF checks, parameterized SQL, and ownership checks on student order pages.

### Key interactions

1. Student searches or filters the menu and adds available food to the cart.
2. Student checks out with cash on pickup or opens the demo UPI screen.
3. Order placement creates database records and a unique `CB` pickup token.
4. Student views the token and follows order status through four stages.
5. Admin changes availability or moves an order to the next preparation stage.
6. Student submits a rating, food review, or suggestion; admin can read it in the dashboard.

## 9. Testing and feedback

The local automated test suite exercises student registration and sign-in, menu search, quantity changes, item removal and cart clearing, cash checkout, demo UPI completion, token generation, order history and tracking, admin login and menu operations, order status updates, and feedback storage/review.

No external student feedback has been collected for this build. The next validation round should ask students to complete realistic tasks on their own phones and record:

- Time from menu open to successful order placement.
- Whether users understand cash pending status and the simulated UPI disclaimer.
- Whether the token and status stages make pickup clear.
- Any accessibility, language, or connectivity barriers.

## 10. Improvements

Prototype improvements already included in the implementation:

- Guest carts carry over when the student registers or signs in.
- Sold-out dishes remain visible but cannot be added.
- UPI demo orders are held until the student completes the simulated payment step.
- Order pages verify the signed-in student owns the requested order.
- Menu images have a visual fallback when remote images cannot load.
- The interface uses responsive navigation and a layout suited to narrow screens.

Further improvements should follow research rather than assumption: validate pickup timing, add dietary and allergen information, test keyboard and screen reader behavior, and review staff workflows during an actual rush.

## 11. Conclusion

CampusBite demonstrates an end-to-end way to move campus canteen ordering from a counter-only interaction into a lightweight digital flow. The prototype includes real SQLite-backed accounts, carts, orders, payments (with simulation only), tracking, feedback, and admin controls. It is ready for local demonstration and guided usability testing; it is not evidence by itself that wait times have already been reduced in a live canteen.

## 12. Future scope

- Run interviews and peak-hour observation at the target campus.
- Pilot with one canteen and measure actual queue and pickup times.
- Add college identity verification, accessible language options, dietary information, and real-time stock controls.
- Add kitchen display and notifications when pickup is ready.
- Evaluate demand forecasting only after enough reliable order data exists.
- Prepare production operations with secure secrets, deployment controls, data retention, backups, and privacy review.
