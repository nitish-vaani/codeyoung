import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/home";
import History from './pages/history'
import SignIn from "./pages/sign-in";
import Dashboard from "./pages/dashboard";
// import ChatPage from "./pages/chat";
import PrivateRoute from "./components/private-route";
import FloatingChatWidget from "./components/FloatingChatWidget"; // NEW
import { pagePaths } from "./common/constants";
import './App.css'
import Header from "./components/header";
import Feedback from './pages/feedback'
import Footer from "./components/footer";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path={pagePaths.signin} element={<SignIn />} />
        <Route
          path={pagePaths.landing}
          element={
            <PrivateRoute>
              <Header/>
              <Home />
              <Footer/>
              <FloatingChatWidget /> {/* NEW: Add widget */}
            </PrivateRoute>
          }
        />
        <Route
          path={pagePaths.home}
          element={
            <PrivateRoute>
              <Header/>
              <Home />
              <Footer/>
              <FloatingChatWidget /> {/* NEW: Add widget */}
            </PrivateRoute>
          }
        />
        <Route
          path={pagePaths.dashboard}
          element={
            <PrivateRoute>
              <Header/>
              <Dashboard />
              <Footer/>
              <FloatingChatWidget /> {/* NEW: Add widget */}
            </PrivateRoute>
          }
        />
        <Route
          path={pagePaths.history}
          element={
            <PrivateRoute>
               <Header/>
              <History />
              <Footer/>
              <FloatingChatWidget />
            </PrivateRoute>
          }
        />
        <Route
          path={pagePaths.feedback}
          element={
            <PrivateRoute>
               <Header/>
              <Feedback />
              <Footer/>
              <FloatingChatWidget />
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
};

export default App;