"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts";
import {
  Search,
  BarChart3,
  MessageSquare,
  CreditCard,
  Users,
  Diamond,
  ShoppingCart,
  FileText,
  Mail,
  Settings,
  ChevronDown,
  MoreHorizontal,
  Download,
  Trash2,
  Plus,
  ChevronLeft,
  ChevronRight,
  Info,
  Menu
} from "lucide-react";

// Sample data for the cash flow chart
const cashFlowData = [
  { month: "Jan", value: 45 },
  { month: "Feb", value: 52 },
  { month: "Mar", value: 48 },
  { month: "Apr", value: 58 },
  { month: "May", value: 55 },
  { month: "Jun", value: 62 },
  { month: "Jul", value: 65 },
  { month: "Aug", value: 68 },
  { month: "Sep", value: 70 },
  { month: "Oct", value: 72 },
  { month: "Nov", value: 75 },
  { month: "Dec", value: 78 }
];

// Sample invoice data
const invoices = [
  {
    id: "BF826438-0001",
    customer: "Robert Baratheon",
    status: "Paid",
    date: "5/30/14",
    dueDate: "7/11/19",
    amount: "$928.41"
  },
  {
    id: "ECF17C97-0017",
    customer: "Arlene McCoy",
    status: "Overdue by 1 day",
    date: "6/21/19",
    dueDate: "9/23/16",
    amount: "$396.84"
  },
  {
    id: "FAD83817-0017",
    customer: "Devon Lane",
    status: "Due in 14 days",
    date: "7/11/19",
    dueDate: "3/4/16",
    amount: "$490.51"
  },
  {
    id: "FAD83817-0017",
    customer: "Ronald Richards",
    status: "Partially Paid",
    date: "4/21/12",
    dueDate: "5/27/15",
    amount: "$601.13"
  },
  {
    id: "FD10AC76-0017",
    customer: "Bessie Cooper",
    status: "Due in 14 days",
    date: "8/30/14",
    dueDate: "9/18/16",
    amount: "$450.54"
  },
  {
    id: "ECF17C97-0016",
    customer: "Robert Fox",
    status: "Overdue by 1 day",
    date: "8/21/15",
    dueDate: "7/27/13",
    amount: "$169.43"
  },
  {
    id: "FAD83817-0016",
    customer: "Guy Hawkins",
    status: "Paid",
    date: "1/31/14",
    dueDate: "5/19/12",
    amount: "$948.55"
  },
  {
    id: "BF826438-0001",
    customer: "Courtney Henry",
    status: "Partially Paid",
    date: "5/19/12",
    dueDate: "12/10/13",
    amount: "$293.01"
  },
  {
    id: "BF826438-0001",
    customer: "Jerome Bell",
    status: "Due in 14 days",
    date: "10/6/13",
    dueDate: "9/4/12",
    amount: "$219.78"
  },
  {
    id: "FD10AC76-0017",
    customer: "Dianne Russell",
    status: "Paid",
    date: "12/4/17",
    dueDate: "4/4/18",
    amount: "$767.50"
  }
];

const sidebarItems = [
  { icon: BarChart3, label: "Dashboard", active: false },
  { icon: MessageSquare, label: "Discuss", active: false, hasSubmenu: true },
  { icon: CreditCard, label: "Subscription", active: false },
  { icon: Users, label: "Contact", active: false },
  { icon: Diamond, label: "CRM", active: false },
  { icon: ShoppingCart, label: "Sales", active: false },
  { icon: FileText, label: "Invoice", active: true },
  { icon: Mail, label: "Email Marketing", active: false, hasSubmenu: true },
  { icon: Settings, label: "Settings", active: false }
];

function getStatusBadge(status: string) {
  switch (status) {
    case "Paid":
      return <Badge className="bg-green-100 text-green-800 hover:bg-green-100">{status}</Badge>;
    case "Partially Paid":
      return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">{status}</Badge>;
    case "Due in 14 days":
      return <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100">{status}</Badge>;
    default:
      return <Badge className="bg-red-100 text-red-800 hover:bg-red-100">{status}</Badge>;
  }
}

function MobileSidebar() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="md:hidden">
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-64 bg-slate-900 p-0 text-white">
        <SidebarContent />
      </SheetContent>
    </Sheet>
  );
}

function SidebarContent() {
  return (
    <>
      {/* Logo */}
      <div className="border-b border-slate-800 p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-600">
            <div className="h-4 w-4 rounded-full bg-white"></div>
          </div>
          <span className="text-lg font-semibold text-white">Dashboard</span>
        </div>
      </div>

      {/* Search */}
      <div className="border-b border-slate-800 p-4">
        <div className="relative">
          <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 transform text-slate-400" />
          <Input
            placeholder="Search"
            className="border-slate-700 bg-slate-800 pl-10 text-white placeholder:text-slate-400"
          />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {sidebarItems.map((item, index) => (
            <li key={index}>
              <div
                className={`flex cursor-pointer items-center justify-between rounded-lg p-3 transition-colors ${
                  item.active
                    ? "bg-slate-800 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}>
                <div className="flex items-center gap-3">
                  <item.icon className="h-5 w-5" />
                  <span className="font-medium">{item.label}</span>
                </div>
                {item.hasSubmenu && <ChevronDown className="h-4 w-4" />}
              </div>
            </li>
          ))}
        </ul>
      </nav>

      {/* User Profile */}
      <div className="border-t border-slate-800 p-4">
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10">
            <AvatarImage src="/professional-headshot.png" />
            <AvatarFallback>DS</AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <div className="text-sm font-medium text-white">Darrell Steward</div>
            <div className="text-xs text-slate-400">darrell@example.com</div>
          </div>
          <MoreHorizontal className="h-4 w-4 text-slate-400" />
        </div>
      </div>
    </>
  );
}

export default function PaymentDashboard() {
  return (
    <div className="bg-background flex h-screen">
      {/* Desktop Sidebar */}
      <div className="hidden w-64 flex-col bg-slate-900 md:flex">
        <SidebarContent />
      </div>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="border-b p-4 md:p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <MobileSidebar />
              <h1 className="text-xl font-semibold md:text-2xl">Invoice</h1>
            </div>
            <Select defaultValue="30days">
              <SelectTrigger className="w-32 md:w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="30days">Last 30 Days</SelectItem>
                <SelectItem value="60days">Last 60 Days</SelectItem>
                <SelectItem value="90days">Last 90 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-4 md:p-6">
          <div className="mb-6 grid grid-cols-1 gap-4 md:mb-8 md:gap-6 xl:grid-cols-4">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6 lg:grid-cols-3 xl:col-span-3">
              <Card>
                <CardContent className="p-4 md:p-6">
                  <div className="mb-2 flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-purple-500"></div>
                    <span className="text-muted-foreground text-sm">Total Invoices</span>
                  </div>
                  <div className="mb-1 text-2xl font-bold text-gray-900 md:text-3xl">$152.9k</div>
                  <div className="text-sm text-green-600">+15.0 /month</div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4 md:p-6">
                  <div className="mb-2 flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-green-500"></div>
                    <span className="text-muted-foreground text-sm">Paid Invoices</span>
                  </div>
                  <div className="mb-1 text-2xl font-bold text-gray-900 md:text-3xl">$109.3k</div>
                  <div className="text-sm text-green-600">+10.47 /month</div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4 md:p-6">
                  <div className="mb-2 flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-orange-500"></div>
                    <span className="text-muted-foreground text-sm">Pending Invoices</span>
                  </div>
                  <div className="mb-1 text-2xl font-bold text-gray-900 md:text-3xl">$43k</div>
                  <div className="text-sm text-green-600">+0.78 /month</div>
                </CardContent>
              </Card>
            </div>

            {/* Total Receivables */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-muted-foreground flex items-center gap-2 text-sm font-medium">
                  Total Receivables
                  <Info className="h-4 w-4" />
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="mb-2 text-xs text-gray-500">Total Unpaid Invoices $43,078</div>
                <div className="bg-muted mb-4 h-2 w-full rounded-full">
                  <div className="h-2 rounded-full bg-purple-600" style={{ width: "62%" }}></div>
                </div>
                <div className="mb-3 text-xs text-gray-500">CURRENT/OVERDUE</div>
                <div className="flex justify-between">
                  <div>
                    <div className="text-lg font-semibold">$109.1k</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold">$65k</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="mb-6 grid grid-cols-1 gap-4 md:mb-8 md:gap-6 xl:grid-cols-4">
            {/* Cash Flow Chart */}
            <Card className="xl:col-span-3">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base font-semibold md:text-lg">
                    Cash Flow
                    <Info className="h-4 w-4 text-gray-400" />
                  </CardTitle>
                  <MoreHorizontal className="h-5 w-5 text-gray-400" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="mb-4 h-48 md:h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={cashFlowData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        dataKey="month"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 12, fill: "#666" }}
                      />
                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fontSize: 12, fill: "#666" }}
                      />
                      <Area
                        type="monotone"
                        dataKey="value"
                        stroke="#8b5cf6"
                        strokeWidth={2}
                        fill="url(#colorGradient)"
                      />
                      <defs>
                        <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.05} />
                        </linearGradient>
                      </defs>
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Cash Flow Summary */}
            <Card>
              <CardContent className="p-4 md:p-6">
                <div className="mb-2 text-xs text-gray-500">Cash as on 04/01/2019</div>
                <div className="mb-4 text-xl font-bold text-gray-900 md:text-2xl">$691.9k</div>

                <div className="space-y-3">
                  <div>
                    <div className="mb-1 text-xs text-green-600">Incoming</div>
                    <div className="text-lg font-semibold">$106.6k</div>
                  </div>
                  <div>
                    <div className="mb-1 text-xs text-red-600">Outgoing</div>
                    <div className="text-lg font-semibold">$798.5k</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* All Invoices Table */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                <CardTitle className="flex items-center gap-2 text-base font-semibold md:text-lg">
                  All Invoices
                  <Info className="h-4 w-4 text-gray-400" />
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Button className="bg-purple-600 text-sm hover:bg-purple-700">
                    <Plus className="mr-2 h-4 w-4" />
                    <span className="hidden sm:inline">New Invoice</span>
                    <span className="sm:hidden">New</span>
                  </Button>
                  <MoreHorizontal className="h-5 w-5 text-gray-400" />
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[800px]">
                  <thead className="bg-muted border-b">
                    <tr>
                      <th className="text-muted-foreground p-3 text-left text-xs font-medium md:p-4 md:text-sm">
                        Invoice Number
                      </th>
                      <th className="text-muted-foreground p-3 text-left text-xs font-medium md:p-4 md:text-sm">
                        Customer Name
                      </th>
                      <th className="text-muted-foreground p-3 text-left text-xs font-medium md:p-4 md:text-sm">
                        Status
                      </th>
                      <th className="text-muted-foreground p-3 text-left text-xs font-medium md:p-4 md:text-sm">
                        Date
                      </th>
                      <th className="text-muted-foreground p-3 text-left text-xs font-medium md:p-4 md:text-sm">
                        Due Date
                      </th>
                      <th className="text-muted-foreground p-3 text-left text-xs font-medium md:p-4 md:text-sm">
                        Amount
                      </th>
                      <th className="text-muted-foreground p-3 text-left text-xs font-medium md:p-4 md:text-sm">
                        Download
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoices.map((invoice, index) => (
                      <tr key={index} className="hover:bg-muted border-b">
                        <td className="p-3 md:p-4">
                          <span className="text-sm font-medium text-blue-600">{invoice.id}</span>
                        </td>
                        <td className="p-3 text-sm md:p-4">{invoice.customer}</td>
                        <td className="p-3 md:p-4">{getStatusBadge(invoice.status)}</td>
                        <td className="text-muted-foreground p-3 text-sm md:p-4">{invoice.date}</td>
                        <td className="text-muted-foreground p-3 text-sm md:p-4">
                          {invoice.dueDate}
                        </td>
                        <td className="p-3 text-sm font-medium text-gray-900 md:p-4">
                          {invoice.amount}
                        </td>
                        <td className="p-3 md:p-4">
                          <div className="flex items-center gap-1">
                            <Button variant="ghost" size="sm">
                              <Download className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex flex-col items-center justify-between gap-4 border-t p-4 sm:flex-row">
                <Button variant="ghost" className="flex items-center gap-2 text-sm">
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>

                <div className="flex items-center gap-1 md:gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="bg-purple-600 text-white hover:bg-purple-700">
                    1
                  </Button>
                  <Button variant="ghost" size="sm">
                    2
                  </Button>
                  <Button variant="ghost" size="sm">
                    3
                  </Button>
                  <span className="hidden text-gray-400 sm:inline">...</span>
                  <Button variant="ghost" size="sm" className="hidden sm:inline-flex">
                    8
                  </Button>
                  <Button variant="ghost" size="sm" className="hidden sm:inline-flex">
                    9
                  </Button>
                  <Button variant="ghost" size="sm">
                    10
                  </Button>
                </div>

                <Button variant="ghost" className="flex items-center gap-2 text-sm">
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  );
}
