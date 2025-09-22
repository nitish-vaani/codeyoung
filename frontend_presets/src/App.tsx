// import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
// import Home from "./pages/home";
// import History from './pages/history'
// import SignIn from "./pages/sign-in";
// import Dashboard from "./pages/dashboard";
// // import ChatPage from "./pages/chat";
// import PrivateRoute from "./components/private-route";
// import FloatingChatWidget from "./components/FloatingChatWidget"; // NEW
// import { pagePaths } from "./common/constants";
// import './App.css'
// import Header from "./components/header";
// import Feedback from './pages/feedback'
// import Footer from "./components/footer";

// const App = () => {
//   return (
//     <Router>
//       <Routes>
//         <Route path={pagePaths.signin} element={<SignIn />} />
//         <Route
//           path={pagePaths.landing}
//           element={
//             <PrivateRoute>
//               <Header/>
//               <Home />
//               <Footer/>
//               <FloatingChatWidget /> {/* NEW: Add widget */}
//             </PrivateRoute>
//           }
//         />
//         <Route
//           path={pagePaths.home}
//           element={
//             <PrivateRoute>
//               <Header/>
//               <Home />
//               <Footer/>
//               <FloatingChatWidget /> {/* NEW: Add widget */}
//             </PrivateRoute>
//           }
//         />
//         <Route
//           path={pagePaths.dashboard}
//           element={
//             <PrivateRoute>
//               <Header/>
//               <Dashboard />
//               <Footer/>
//               <FloatingChatWidget /> {/* NEW: Add widget */}
//             </PrivateRoute>
//           }
//         />
//         <Route
//           path={pagePaths.history}
//           element={
//             <PrivateRoute>
//                <Header/>
//               <History />
//               <Footer/>
//               <FloatingChatWidget />
//             </PrivateRoute>
//           }
//         />
//         <Route
//           path={pagePaths.feedback}
//           element={
//             <PrivateRoute>
//                <Header/>
//               <Feedback />
//               <Footer/>
//               <FloatingChatWidget />
//             </PrivateRoute>
//           }
//         />
//       </Routes>
//     </Router>
//   );
// };

// export default App;




// frontend/src/App.tsx
// Updated to use simple configuration - minimal changes to your existing code

import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/home";
import History from './pages/history'
import SignIn from "./pages/sign-in";
import Dashboard from "./pages/dashboard";
import PrivateRoute from "./components/private-route";
import FloatingChatWidget from "./components/FloatingChatWidget";
import Header from "./components/header";
import Feedback from './pages/feedback'
import Footer from "./components/footer";
import { CONFIG} from "./config/appConfig";
import './App.css'

const App = () => {
  // Get default redirect based on enabled pages
  const getDefaultRedirect = (): string => {
    if (CONFIG.pages.call_test) return "/home";
    if (CONFIG.pages.dashboard) return "/dashboard";
    if (CONFIG.pages.call_history) return "/history";
    if (CONFIG.pages.feedback) return "/feedback";
    return "/sign-in";
  };

  return (
    <Router>
      <Routes>
        {/* Sign In Route - Only if enabled */}
        {CONFIG.pages.signin && (
          <Route path="/sign-in" element={<SignIn />} />
        )}
        
        {/* Home/Call Test Routes - Only if enabled */}
        {CONFIG.pages.call_test && (
          <>
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Header/>
                  <Home />
                  {CONFIG.components.global.footer && <Footer/>}
                  {CONFIG.components.global.floating_chat_widget && <FloatingChatWidget />}
                </PrivateRoute>
              }
            />
            <Route
              path="/home"
              element={
                <PrivateRoute>
                  <Header/>
                  <Home />
                  {CONFIG.components.global.footer && <Footer/>}
                  {CONFIG.components.global.floating_chat_widget && <FloatingChatWidget />}
                </PrivateRoute>
              }
            />
          </>
        )}
        
        {/* Dashboard Route - Only if enabled */}
        {CONFIG.pages.dashboard && (
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Header/>
                <Dashboard />
                {CONFIG.components.global.footer && <Footer/>}
                {CONFIG.components.global.floating_chat_widget && <FloatingChatWidget />}
              </PrivateRoute>
            }
          />
        )}
        
        {/* History Route - Only if enabled */}
        {CONFIG.pages.call_history && (
          <Route
            path="/history"
            element={
              <PrivateRoute>
                <Header/>
                <History />
                {CONFIG.components.global.footer && <Footer/>}
                {CONFIG.components.global.floating_chat_widget && <FloatingChatWidget />}
              </PrivateRoute>
            }
          />
        )}
        
        {/* Feedback Route - Only if enabled */}
        {CONFIG.pages.feedback && (
          <Route
            path="/feedback"
            element={
              <PrivateRoute>
                <Header/>
                <Feedback />
                {CONFIG.components.global.footer && <Footer/>}
                {CONFIG.components.global.floating_chat_widget && <FloatingChatWidget />}
              </PrivateRoute>
            }
          />
        )}

        {/* Fallback route */}
        <Route path="*" element={<Navigate to={getDefaultRedirect()} replace />} />
      </Routes>
    </Router>
  );
};

export default App;