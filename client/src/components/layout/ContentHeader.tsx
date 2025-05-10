import { AppBreadcrumb } from "./AppBreadcrumb";

export function ContentHeader({ children }: { children?: React.ReactNode }) {
  return (
    <div className="px-2 mt-1 mb-2 flex items-center gap-4">
      <AppBreadcrumb />
      {children && <div className="ml-auto space-x-4">{children}</div>}
    </div>
  );
}
