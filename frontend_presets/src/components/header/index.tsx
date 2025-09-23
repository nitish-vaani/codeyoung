// frontend/src/components/header/index.tsx
import { useNavigate } from "react-router-dom";
import sbi from "../../assets/logos/sbi.png"
import avatar from "../../assets/logos/user_gray.png"
import { Menubar } from "primereact/menubar";
import { Badge } from "primereact/badge";
import { CONFIG, menuItems} from "../../config/appConfig";

const Header = () => {
  const navigate = useNavigate();
  const name = localStorage.getItem("Name");

  const itemRenderer = (item: any) => (
    <a className="p-menuitem-link" onClick={handleLogout}>
      <span className={item.icon} />
      <span className="mx-2">{item.label}</span>
      {item.badge && <Badge className="ml-auto" value={item.badge} />}
      {item.shortcut && <span className="ml-auto border-1 surface-border border-round surface-100 text-xs p-1">{item.shortcut}</span>}
    </a>
  );

  // User dropdown - only show if enabled
  const userMenuItems = CONFIG.components.header.user_avatar_dropdown ? [
    {
      label: name || "Guest",
      items: [{
        label: 'Sign out',
        template: itemRenderer
      }]
    }
  ] : [];

  const handleLogout = () => {
    localStorage.clear();
    navigate("/sign-in");
  };

  const start = CONFIG.components.header.user_avatar_dropdown 
    ? <img className="avatar-user" src={avatar} alt="" />
    : null;

  // Don't render header if no menu items or user dropdown
  if (menuItems.length === 0 && !CONFIG.components.header.user_avatar_dropdown) {
    return null;
  }

  return (
    <div className="home">
      <section className="header">
        <img className="sbi-home" src={sbi} />
        
        {/* Only show menu if there are menu items */}
        {menuItems.length > 0 && (
          <div className="menu">
            <Menubar model={menuItems} />
          </div>
        )}
        
        {/* Only show user avatar if enabled */}
        {CONFIG.components.header.user_avatar_dropdown && (
          <div className="avatar">
            <div className="card">
              <Menubar start={start} model={userMenuItems} />
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default Header;