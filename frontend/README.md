# Techbank.Ai - Frontend Application

A modern, animated React frontend for the Techbank.Ai resume screening platform.

## Features

- 🎨 **Modern UI** - Beautiful, gradient-based design with smooth animations
- 🚀 **Fast & Responsive** - Built with Vite for optimal performance
- 📱 **Mobile Friendly** - Responsive design that works on all devices
- ✨ **Animations** - Smooth transitions using Framer Motion
- 🔐 **Authentication** - Login system with route protection
- 📄 **CV Upload** - Drag & drop file upload with validation
- 📝 **Form Handling** - Comprehensive personal information form
- 👤 **User Profile** - Profile button with avatar
- ⚙️ **Admin Toggle** - Admin functionality (ready for future implementation)

## Tech Stack

- **React 18** - UI library
- **React Router 6** - Routing
- **Framer Motion** - Animations
- **Vite** - Build tool
- **CSS3** - Styling with modern features

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Project Structure

```
src/
├── components/
│   ├── Navbar.jsx          # Navigation bar component
│   └── Navbar.css
├── pages/
│   ├── Login.jsx           # Login page
│   ├── Dashboard.jsx      # Main dashboard
│   ├── EmploymentTypeSelection.jsx  # Employment type selection
│   ├── CVUpload.jsx       # CV/Resume upload page
│   └── PersonalInfo.jsx   # Personal information form
├── config/
│   └── api.js             # API configuration and reminders
├── App.jsx                 # Main app component with routing
├── main.jsx               # Entry point
└── index.css              # Global styles
```

## Routes

- `/login` - Login page
- `/dashboard` - Main dashboard with employment type selection
- `/application` - Combined CV upload and personal information form

See `ROUTES.md` for detailed route documentation.

## API Integration

The application is ready for API integration. See `src/config/api.js` for:
- API endpoint configuration
- Helper functions
- Integration TODO list

**Important**: Update `API_BASE_URL` in `src/config/api.js` with your backend URL.

## Employment Types

The application supports 4 employment types:
1. **Company Employee** - Full-time or part-time employee
2. **Hired Forces** - Contractor or temporary workforce
3. **Freelancer** - Independent contractor or self-employed
4. **Guest User** - Temporary or guest access

## Features in Detail

### Dashboard
- Beautiful gradient background
- Navbar with "Techbank.Ai" heading
- Profile button with user avatar
- Admin toggle button
- 4 employment type cards directly on dashboard:
  - Company Employee
  - Hired Forces
  - Freelancer
  - Guest User
- Creative card-based selection (not dropdown)
- Animated hover effects
- Visual feedback on selection
- Auto-navigation to application page

### Application Page
- **CV Upload Section**:
  - Drag & drop interface
  - File type validation (PDF, DOC, DOCX)
  - File size validation (max 5MB)
  - File preview with remove option
- **Personal Information Form**:
  - Comprehensive form with sections:
    - Basic Information
    - Address
    - Professional Information
    - Links
  - Form validation
  - Responsive layout
- Single submit button for both CV and personal info
- All on one page for seamless experience

## Environment Variables

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=http://localhost:5000/api
```

## TODO / Reminders

### API Integration
- [ ] Implement login API call
- [ ] Implement CV upload API
- [ ] Implement application submission API
- [ ] Add error handling
- [ ] Add loading states
- [ ] Implement token refresh
- [ ] Add logout functionality

### Features
- [ ] Implement admin functionality
- [ ] Add profile page
- [ ] Add application history page
- [ ] Add file download functionality
- [ ] Add form data persistence

### Improvements
- [ ] Add state management (Context API/Redux)
- [ ] Add form validation library
- [ ] Add toast notifications
- [ ] Add error boundaries
- [ ] Add unit tests
- [ ] Add E2E tests

## Development

The app runs on `http://localhost:3000` by default.

## Production Build

```bash
npm run build
```

The build output will be in the `dist` folder.

## License

MIT

