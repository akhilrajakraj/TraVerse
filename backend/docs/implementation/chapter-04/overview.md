# Chapter 04 — Accounts Application

## Overview

Chapter 04 introduces the authentication foundation of the TraVerse platform.

Unlike the previous chapter, which focused on reusable infrastructure, this chapter implements the first domain-specific application responsible for user authentication and identity management.

The Accounts application establishes the project's custom authentication architecture and provides the foundation upon which every subsequent application will build.

All future domain models—including Travelers, Destinations, Trips, Planner, Bookings, Payments, and Documents—will reference the custom user model implemented during this chapter.

---

# Objectives

The primary objectives of this chapter were:

- Implement a custom Django User model.
- Replace Django's default authentication model.
- Configure email-based authentication.
- Introduce JWT authentication using Django REST Framework SimpleJWT.
- Implement user registration.
- Implement user login.
- Implement authenticated user retrieval.
- Configure Django Admin for the custom user model.
- Establish a scalable authentication architecture for the entire platform.

---

# Scope

The implementation includes:

- Custom UserManager
- Custom User model
- UUID primary key strategy
- Email-based authentication
- JWT configuration
- Global authentication settings
- Account-specific exceptions
- Registration serializer
- Login serializer
- User serializer
- Registration API
- Login API
- Logout API
- Current User API
- Django Admin integration
- Initial database migration
- Comprehensive automated testing

---

# Major Architectural Decisions

Several important architectural decisions were made during this chapter.

## Custom User Model

Instead of relying on Django's built-in `auth.User`, the project introduces a dedicated custom user model.

This decision provides complete control over authentication while avoiding future migration limitations.

---

## Email Authentication

Email replaces the traditional username as the primary authentication identifier.

This simplifies authentication for end users and aligns with modern web application practices.

---

## UUID Primary Keys

The project adopts UUID primary keys for the User model.

This decision aligns the Accounts application with the reusable UUID infrastructure established during Chapter 03 and provides a consistent identifier strategy across the platform.

---

## JWT Authentication

Authentication is implemented using JSON Web Tokens.

JWT enables stateless authentication suitable for REST APIs while supporting future mobile and frontend clients.

---

## Global Authentication Configuration

Authentication configuration is centralized within the project settings rather than individual applications.

Future applications automatically inherit the authentication infrastructure without additional configuration.

---

# Future Consumers

The authentication infrastructure introduced during this chapter will be consumed by every remaining domain application.

Examples include:

| Application | Dependency |
|------------|------------|
| Travelers | User ownership |
| Destinations | Creator tracking |
| Trips | Trip ownership |
| Planner | Personal plans |
| Documents | Uploaded by user |
| Bookings | Customer relationship |
| Payments | Payment ownership |
| Notifications | Recipient tracking |

No future application should implement its own authentication model.

The Accounts application remains the single source of truth for user identity throughout the TraVerse platform.

---

# Outcome

By the conclusion of Chapter 04, the project possesses a fully functional authentication system built upon a custom UUID-based User model.

The authentication architecture has been validated through automated testing and serves as the permanent identity foundation for the remainder of the TraVerse platform.