import PanelButton from "./components/PanelButton";
import Panel from "./components/Panel/Panel";
import { useState } from "react";
import { useColorMode } from "./theme/ThemeContext";

const App = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { mode, toggleColorMode } = useColorMode();

  const isDarkMode = mode === "dark";

  const togglePanel = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div
      style={{
        zIndex: 99999,
        fontFamily: "sans-serif",
      }}
    >
      <Panel
        isOpen={isOpen}
        toggleChat={togglePanel}
        isDarkMode={isDarkMode}
        onToggleDarkMode={toggleColorMode}
      />
      <PanelButton isOpen={isOpen} toggleChat={togglePanel} />
    </div>
  );
};

export default App;
