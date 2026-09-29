# Project Charter: Fridgely

## 1. Project Purpose and Objectives

Fridgely is a web-based assistant that lets users manually add ingredients they have at home and view the dates they were added. It generates AI-powered recipes based on those ingredients and users’ dietary and allergen preferences, provides cooking times and calorie information, and adds missing ingredients to a smart shopping list with one click. It also saves favorite recipes and previously viewed recipes. The project aims to reduce food waste, suggest practical meals using ingredients already at home, and apply the full software engineering lifecycle, from requirements through testing.

## 2. Stakeholders & Roles

Potential Customers & End-Users:Target end-users include university students living in dorms or apartments, busy young professionals who want to cook with limited ingredients at home, and health-conscious individuals following specific dietary restrictions (such as gluten-free or lactose-free). Overall, the system is designed for individuals who want to manage their available food ingredients, discover recipes based on what they have at home, reduce food waste, and receive personalized recipe suggestions tailored to their specific dietary preferences and allergies.

**Product Owner:** İrem Demircan

**Software Engineering Team:** Team members and their roles (include the project manager as Member 1)

- **Berfin Gökgöz:** Full-Stack and Database Developer (database schema, basic authentication and JWT, and data architecture)

- **İrem Demircan:** Backend Developer 1 (fridge inventory CRUD services and tracking the dates ingredients were added)

- **Sarp Çizer:** Backend Developer 2 (shopping list, favorites, recipe history, and general API support services)

- **Ayşe Döne:** AI Integration Developer (generative AI API integration, prompt engineering for recipes, calories, and cooking times, and pipeline management)

- **Mustafa Safa Bayrak:** Frontend Developer (UI/UX design, interface components built with Tailwind CSS, and API integration)

- **Kerem Sönmez:** DevOps and QA Developer (quality assurance, unit and functional tests using TDD, CI/CD pipeline, and cloud deployment)

**GitHub Repository/Project URL:** https://github.com/SarpCizer/CMPE331-Project

## 3. Project Scope

### Project domain

Food, Home, and Lifestyle / Smart Kitchen Assistants. Potential customers and end users include people who do not want to spend time deciding what to cook, students living in shared housing, people seeking to reduce food waste by using ingredients they already have, and home cooks with specific dietary or allergen restrictions.

### In Scope

- **User Management and Authentication:** Users can register and sign in with an email address and password (basic authentication without email verification) and save dietary and allergen preferences to their profiles.

- **Fridge and Inventory Management:** Users can manually add, delete, and list ingredients in their fridge and view the dates those ingredients were added.

- **AI-Powered Recipe Generation:** Ingredients in the fridge and dietary filters are sent to an AI service to generate recipes with step-by-step instructions, cooking times, and calorie information.

- **Smart Shopping List:** Users can add missing recipe ingredients to a smart shopping list with one click and manage them there.

- **Favorites and History:** Users can save recipes they like as favorites and view a list of previously viewed recipes.

### Out of Scope

- **Receipt Scanning / OCR:** Uploading receipt photos for automatic AI-based item recognition and inventory entry (excluded from the initial release; users will enter items manually).

- **Expiration Date Tracking / Alerts:** Tracking product expiration dates and issuing automatic spoilage alerts.

- **Automatic Inventory Deduction:** Automatically removing used ingredients from the fridge when a selected recipe is cooked (ingredient tracking will rely entirely on manual additions and deletions).

- **Native Mobile App:** Developing a native iOS or Android app (responsive web design is in scope).

## 4. Technology Stack

### Backend Stack

- Node.js / Express.js (or Python FastAPI)

- PostgreSQL (relational database) / MongoDB

- JWT (JSON Web Token) for authentication

### Frontend Stack

- React.js / Next.js

- Tailwind CSS (modern, responsive interface design)

- Axios (API communication)

### AI Stack

- OpenAI API / Anthropic Claude API (recipe, calorie, and cooking-time generation and prompt engineering)

- LLM Prompt Pipelines & Response Parsing

## 5. Project Milestones

| Deliverable | Deadline |
| --- | --- |
| Project Charter | 02.10.2026 23:59 |
| Requirements Definition Report | 11.10.2026 23:59 |
| Requirement Analysis Report | 18.10.2026 23:59 |
| Software Design Report | 15.11.2026 23:59 |
| Software Testing Report | 22.11.2026 23:59 |
| Codebase | 30.11.2026 23:59 |
| Presentation | TBA (see sched.) |
