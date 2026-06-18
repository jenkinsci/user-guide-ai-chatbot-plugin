
export default function SidePanel({
  toggleChat,
  isOpen,
}: {
  toggleChat: () => void;
  isOpen: boolean;
}) {
  return (
    isOpen && (
    // @ts-ignore
      <div style={styles.chatWindow}>
        <div style={styles.header}>
          <strong>AI Assistant</strong>
          <button onClick={toggleChat} style={styles.closeBtn}>
            X
          </button>
        </div>
        <div style={styles.body}>
          <p>Bot enabled</p>
        </div>
      </div>
    )
  );
}

const styles = {
  floatBtn: {
    position: "absolute",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    bottom: "20px",
    right: "20px",
    width: "60px",
    height: "60px",
    borderRadius: "50%",
    backgroundColor: "#000000",
    color: "white",
    border: "none",
    fontSize: "24px",
    cursor: "pointer",
    boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
  },
  chatWindow: {
    color: "#000000",
    position: "absolute",
    bottom: 0,
    right: 0,
    width: "400px",
    height: "100vh",
    backgroundColor: "white",
    border: "1px solid #ccc",
    boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    zIndex: 1,
  },
  header: {
    padding: "10px",
    background: "#f5f5f5",
    borderBottom: "1px solid #ddd",
    display: "flex",
    justifyContent: "space-between",
  },
  body: {
    padding: "10px",
    flex: 1,
    overflow: "auto",
  },
  closeBtn: {
    background: "transparent",
    border: "none",
    cursor: "pointer",
    fontWeight: "bold",
    color: "#000000",
  },
};
