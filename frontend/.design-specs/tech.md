# Technology Stack

## Project Type
This project is a single-page web application (SPA) that provides a frontend for the `ragatouille` API.

## Core Technologies

### Primary Language(s)
- **Language**: **TypeScript** `~5.8.0`
- **Framework**: **Angular** `~20.3.12`
- **Styling**: **SCSS**

### Key Dependencies
- **@angular/common, core, forms, platform-browser, router**: Core Angular framework modules.
- **@angular/cdk, @angular/material**: **Angular Material** (`~20.2.13`) for UI components.
- **rxjs**: `~7.8.0` for reactive programming.
- **@ngneat/until-destroy**: `^10.0.0` for automatic subscription management.
- **zone.js**: `~0.15.0` for Angular's change detection mechanism.

### Application Architecture
- **Component-Based SPA**: The application is built as a single-page application using Angular's component architecture.
- **Client-Server**: It communicates with a backend via a RESTful API. The client is generated from an OpenAPI specification.

## Development Environment

### Build & Development Tools
- **Package Management**: **npm**
- **Build System**: **Angular CLI** (`@angular-devkit/build-angular` `~20.3.10`)
- **Development workflow**: `ng serve` provides a local development server with live reloading.

### Code Quality Tools
- **Static Analysis / Type Checking**: **TypeScript** compiler with `strict` mode enabled (`"strict": true` in `tsconfig.json`).
- **Formatting**: Adherence to Angular's official style guide.
- **Testing Framework**: **Playwright** (`^1.56.1`) for End-to-End (E2E) testing.

### Version Control & Collaboration
- **VCS**: **Git**

## Deployment & Distribution
- **Target Platform**: Web browsers.
- **Distribution Method**: The application is built into static files (HTML, CSS, JS) and can be served by any web server or CDN.