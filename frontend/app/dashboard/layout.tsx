import PushSubscriber from "@/components/PushSubscriber";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <PushSubscriber />
      {children}
    </>
  );
}
