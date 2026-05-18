import { useState, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Sheet,
  SheetContent,
  Button,
  Badge,
} from '@/components/ui'
import { DataModeBanner } from '@/components/DataModeBanner'
import {
  Home,
  History,
  AlertTriangle,
  Menu,
  Shield,
  Activity,
  Sun,
  Moon,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAnalysis } from '@/lib/context/AnalysisContext'
import { useTheme } from '@/lib/context/ThemeContext'

interface NavItem {
  id: string
  label: string
  icon: React.ReactNode
  path: string
  badge?: number
}

const baseNavItems: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Home',
    icon: <Home className="h-5 w-5" />,
    path: '/',
  },
  {
    id: 'history',
    label: 'History',
    icon: <History className="h-5 w-5" />,
    path: '/history',
  },
]

function Sidebar() {
  const location = useLocation()
  const { latestAnalysis } = useAnalysis()

  const violationCount = useMemo(() => {
    if (!latestAnalysis?.validationResult?.findings) return undefined
    const findings = latestAnalysis.validationResult.findings
    if (!Array.isArray(findings)) return undefined
    const count = findings.filter((f: any) => f && !f.passed).length
    return count > 0 ? count : undefined
  }, [latestAnalysis])

  const navItems = useMemo(() => {
    return baseNavItems.map((item) =>
      item.id === 'violations' ? { ...item, badge: violationCount } : item
    )
  }, [violationCount])

  return (
     <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:border-r lg:border-border lg:bg-card lg:h-screen lg:sticky lg:top-0">
       <div className="p-4 border-b border-border">
         <Link to="/" className="flex items-center gap-3">
           <div className="p-2 bg-primary/10 rounded-lg">
             <Shield className="h-6 w-6 text-primary" />
           </div>
           <div>
             <h1 className="font-semibold text-foreground text-lg font-heading">
               MED-THERM
             </h1>
             <p className="text-xs text-muted-foreground">Compliance Engine</p>
           </div>
         </Link>
       </div>

       <nav className="flex-1 p-4 space-y-1">
         {navItems.map((item) => {
           const isActive = location.pathname === item.path
           return (
             <Link
               key={item.id}
               to={item.path}
               className={cn(
                 'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all touch-target',
                 isActive
                   ? 'bg-primary/10 text-primary'
                   : 'text-muted-foreground hover:bg-muted hover:text-foreground'
               )}
               aria-current={isActive ? 'page' : undefined}
             >
               {item.icon}
               <span>{item.label}</span>
               {item.badge !== undefined && item.badge > 0 && (
                 <Badge
                   variant={item.badge > 2 ? 'destructive' : 'secondary'}
                   className="ml-auto"
                 >
                   {item.badge}
                 </Badge>
               )}
             </Link>
           )
         })}
       </nav>

       <div className="p-4 border-t border-border">
         <div className="flex items-center gap-3 p-3 bg-muted/40 rounded-lg">
           <div className="flex-shrink-0 w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center">
             <Activity className="h-5 w-5 text-primary" />
           </div>
           <div className="flex-1 min-w-0">
             <p className="text-sm font-medium text-foreground">
               System Status
             </p>
             <p className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
               <span className="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full animate-pulse" />
               Connected
             </p>
           </div>
         </div>
       </div>
     </aside>
  )
}

function MobileNav({ open, setOpen }: { open: boolean; setOpen: (open: boolean) => void }) {
  const location = useLocation()
  const { latestAnalysis } = useAnalysis()

  const violationCount = useMemo(() => {
    if (!latestAnalysis?.validationResult?.findings) return undefined
    const findings = latestAnalysis.validationResult.findings
    if (!Array.isArray(findings)) return undefined
    const count = findings.filter((f: any) => f && !f.passed).length
    return count > 0 ? count : undefined
  }, [latestAnalysis])

  const navItems = useMemo(() => {
    return baseNavItems.map((item) =>
      item.id === 'violations' ? { ...item, badge: violationCount } : item
    )
  }, [violationCount])

   return (
     <Sheet open={open} onOpenChange={setOpen}>
       <SheetContent side="left" className="w-[280px] sm:w-[320px] p-0">
         <div className="p-4 border-b border-border">
           <Link
             to="/"
             onClick={() => setOpen(false)}
             className="flex items-center gap-3"
           >
             <div className="p-2 bg-primary/10 rounded-lg">
               <Shield className="h-6 w-6 text-primary" />
             </div>
             <div>
               <h1 className="font-semibold text-foreground text-lg font-heading">
                 MED-THERM
               </h1>
               <p className="text-xs text-muted-foreground">Compliance Engine</p>
             </div>
           </Link>
         </div>

         <nav className="p-4 space-y-1">
           {navItems.map((item) => {
             const isActive = location.pathname === item.path
             return (
               <Link
                 key={item.id}
                 to={item.path}
                 onClick={() => setOpen(false)}
                 className={cn(
                   'flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-all touch-target',
                   isActive
                     ? 'bg-primary/10 text-primary'
                     : 'text-muted-foreground hover:bg-muted'
                 )}
               >
                 {item.icon}
                 <span>{item.label}</span>
                 {item.badge !== undefined && item.badge > 0 && (
                   <Badge
                     variant={item.badge > 2 ? 'destructive' : 'secondary'}
                     className="ml-auto"
                   >
                     {item.badge}
                   </Badge>
                 )}
               </Link>
             )
           })}
         </nav>

         <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border">
           <div className="flex items-center gap-3 p-3 bg-muted/40 rounded-lg">
             <div className="flex-shrink-0 w-10 h-10 bg-primary/20 rounded-full flex items-center justify-center">
               <Activity className="h-5 w-5 text-primary" />
             </div>
             <div className="flex-1 min-w-0">
               <p className="text-sm font-medium text-foreground">
                 System Status
               </p>
               <p className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                 <span className="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full" />
                 Connected
               </p>
             </div>
           </div>
         </div>
       </SheetContent>
     </Sheet>
   )
 }

 function Header({ onMenuClick }: { onMenuClick: () => void }) {
   const location = useLocation()
   const { theme, toggleTheme } = useTheme()

   const currentPage = baseNavItems.find((item) => item.path === location.pathname)

   return (
     <header className="sticky top-0 z-40 bg-card/80 backdrop-blur-lg border-b border-border">
       <div className="flex items-center justify-between px-4 h-14">
         <div className="flex items-center gap-3">
            <button
              onClick={onMenuClick}
              className="p-2 hover:bg-muted rounded-lg touch-target"
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-primary" />
              <span className="font-semibold text-foreground font-heading">
                {currentPage?.label || 'MED-THERM'}
              </span>
            </div>
         </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 touch-target"
              aria-label="Toggle theme"
              onClick={toggleTheme}
            >
              {theme === 'dark' ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 touch-target"
              aria-label="Notifications"
            >
              <AlertTriangle className="h-5 w-5 text-muted-foreground" />
            </Button>
          </div>
       </div>
     </header>
   )
 }

 interface LayoutProps {
   children: React.ReactNode
 }

 export function Layout({ children }: LayoutProps) {
   const [mobileNavOpen, setMobileNavOpen] = useState(false)

   return (
     <div className="min-h-screen bg-background flex">
       <MobileNav open={mobileNavOpen} setOpen={setMobileNavOpen} />

       <div className="flex-1 flex flex-col min-w-0">
         <Header onMenuClick={() => setMobileNavOpen(true)} />
         <DataModeBanner />
         <main className="flex-1 p-4 sm:p-6 lg:p-8">
           {children}
         </main>

         <footer className="border-t border-border bg-card p-4 text-center">
           <p className="text-xs text-muted-foreground">
             MED-THERM Compliance Engine v0.1.0 • Built for regulatory compliance
           </p>
         </footer>
       </div>
     </div>
   )
 }

export default Layout
