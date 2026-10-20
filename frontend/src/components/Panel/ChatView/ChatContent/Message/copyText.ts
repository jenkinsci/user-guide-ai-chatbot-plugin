export async function copyText(text: string): Promise<boolean> {
  if (window.isSecureContext && navigator.clipboard) {
    try {
      
      await navigator.clipboard.writeText(text);
      return true;

    } catch {
      // Fall back to the older methd below.
    }
  }

  
  const previousFocus = document.activeElement as HTMLElement | null;
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();

  try {

    return document.execCommand("copy");

  } catch {

    return false;
  } finally {

    textarea.remove();
    previousFocus?.focus();

  }
}
