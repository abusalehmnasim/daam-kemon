export interface StoreStyle {
  name: string;
  displayName: string;
  bg: string;
  text: string;
  border: string;
  dot: string;
}

const STORE_STYLES: Record<string, StoreStyle> = {
  chaldal: {
    name: "chaldal",
    displayName: "Chaldal",
    bg: "bg-[#FFF6EB]",
    text: "text-[#B85700]",
    border: "border-[#FFD9B3]",
    dot: "bg-[#FF7F00]",
  },
  shwapno: {
    name: "shwapno",
    displayName: "Shwapno",
    bg: "bg-[#FDF1F1]",
    text: "text-[#C71820]",
    border: "border-[#F9C5C7]",
    dot: "bg-[#E31B23]",
  },
  unimart: {
    name: "unimart",
    displayName: "Unimart",
    bg: "bg-[#EBF7F7]",
    text: "text-[#006666]",
    border: "border-[#B2E2E2]",
    dot: "bg-[#008080]",
  },
  agora: {
    name: "agora",
    displayName: "Agora",
    bg: "bg-[#EEF7F2]",
    text: "text-[#16703D]",
    border: "border-[#BDE5CF]",
    dot: "bg-[#1F8A4C]",
  },
  daraz: {
    name: "daraz",
    displayName: "Daraz",
    bg: "bg-[#FFF3EB]",
    text: "text-[#C24300]",
    border: "border-[#FED2B8]",
    dot: "bg-[#F85606]",
  },
  othoba: {
    name: "othoba",
    displayName: "Othoba",
    bg: "bg-[#EFF6FC]",
    text: "text-[#005CA8]",
    border: "border-[#C4DEF7]",
    dot: "bg-[#0072CE]",
  },
};

export function getStoreStyle(storeName: string): StoreStyle {
  const key = storeName.toLowerCase().trim();
  return (
    STORE_STYLES[key] || {
      name: key,
      displayName: storeName,
      bg: "bg-line/40",
      text: "text-ink",
      border: "border-line",
      dot: "bg-muted",
    }
  );
}

export function StoreBadge({
  storeName,
  displayName,
  size = "md",
}: {
  storeName: string;
  displayName?: string;
  size?: "sm" | "md";
}) {
  const style = getStoreStyle(storeName);
  const name = displayName || style.displayName;

  if (size === "sm") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-semibold tracking-tight transition-transform ${style.bg} ${style.text} ${style.border}`}
      >
        <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} aria-hidden="true" />
        <span className="truncate">{name}</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-semibold tracking-tight ${style.bg} ${style.text} ${style.border}`}
    >
      <span className={`h-2 w-2 rounded-full ${style.dot}`} aria-hidden="true" />
      <span className="truncate">{name}</span>
    </span>
  );
}
