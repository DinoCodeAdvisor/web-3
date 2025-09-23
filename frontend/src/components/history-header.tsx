// components/history-header.tsx
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

import {
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";

const HistoryHeader = () => {
  return (
    <SheetHeader>
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink href="/">Calculator</BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>History</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <SheetTitle>Your History</SheetTitle>
      <SheetDescription>
        This is a list of all the calculations you have made in the past. Expand
        each card to see which operations were used to arrive to the result.
      </SheetDescription>
    </SheetHeader>
  );
};

export default HistoryHeader;
