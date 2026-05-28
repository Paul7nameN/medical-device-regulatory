import { useState, useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Button,
  Badge,
} from '@/components/ui'
import { DataModeBanner } from '@/components/DataModeBanner'
import { ActiveTransportBanner } from '@/components/ActiveTransportBanner'
import {
  Home,
  History,
  Radio,
  AlertTriangle,
  Menu,
  Activity,
  Sun,
  Moon,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAnalysis } from '@/lib/context/AnalysisContext'
import { useTheme } from '@/lib/context/ThemeContext'
import { useLiveTransport } from '@/lib/context/LiveTransportContext'

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
    id: 'live',
    label: 'Live Transport',
    icon: <Radio className="h-5 w-5" />,
    path: '/live',
  },
  {
    id: 'history',
    label: 'History',
    icon: <History className="h-5 w-5" />,
    path: '/history',
  },
]

function Sidebar({ isOpen }: { isOpen: boolean }) {
  const location = useLocation()
  const { latestAnalysis } = useAnalysis()
  const { isRunning, alerts } = useLiveTransport()

  const violationCount = useMemo(() => {
    if (!latestAnalysis?.validationResult?.findings) return undefined
    const findings = latestAnalysis.validationResult.findings
    if (!Array.isArray(findings)) return undefined
    const count = findings.filter((f: any) => f && !f.passed).length
    return count > 0 ? count : undefined
  }, [latestAnalysis])

  const hasLiveAlerts = alerts.length > 0
  const hasCriticalLiveAlerts = alerts.some((a) => a.severity === 'critical' || a.severity === 'high')

  const navItems = useMemo(() => {
    return baseNavItems.map((item) => {
      if (item.id === 'violations') {
        return { ...item, badge: violationCount }
      }
      if (item.id === 'live' && isRunning) {
        return {
          ...item,
          isLive: true,
          liveHasCritical: hasCriticalLiveAlerts,
          badge: hasLiveAlerts ? alerts.length : undefined,
        }
      }
      return item
    })
  }, [violationCount, isRunning, hasLiveAlerts, hasCriticalLiveAlerts, alerts.length])

   return (
      <aside className={cn(
        "flex flex-col border-r border-border bg-card transition-all duration-300 ease-in-out flex-shrink-0 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto",
        isOpen ? "w-64" : "w-20"
      )}>
       <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item: any) => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.id}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all touch-target relative',
                  !isOpen && 'justify-center px-2',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <div className="relative">
                  {item.icon}
                  {item.isLive && (
                    <span className={cn(
                      'absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full animate-pulse',
                      item.liveHasCritical ? 'bg-red-500' : 'bg-primary'
                    )} />
                  )}
                </div>
                {isOpen && (
                  <>
                    <span className="truncate">{item.label}</span>
                    {item.badge !== undefined && item.badge > 0 && (
                      <Badge
                        variant={item.badge > 2 || item.liveHasCritical ? 'critical' : 'secondary'}
                        className="ml-auto flex-shrink-0"
                      >
                        {item.badge}
                      </Badge>
                    )}
                  </>
                )}
              </Link>
            )
          })}
        </nav>

       {isOpen && (
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
       )}
     </aside>
  )
}

function Header({ onMenuClick, sidebarOpen }: { onMenuClick: () => void; sidebarOpen: boolean }) {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()

  const currentPage = baseNavItems.find((item) => item.path === location.pathname)
  const isHome = location.pathname === '/'

  return (
    <header className="sticky top-0 z-50 bg-card/80 backdrop-blur-lg border-b border-border">
      <div className="flex items-center justify-between px-4 h-14">
        <div className="flex items-center gap-3">
           <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9 touch-target"
              aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
              onClick={onMenuClick}
            >
              <Menu className="h-5 w-5" />
            </Button>

            <Link to="/" className="flex items-center gap-2 group">
              <img src="/favicon.png" alt="MED-THERM Logo" className="h-6 w-6" />
              <span className="font-semibold text-foreground font-heading group-hover:underline underline-offset-4">
                MED-THERM
              </span>
            </Link>

            {!isHome && currentPage && (
              <>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium text-foreground">
                  {currentPage.label}
                </span>
              </>
            )}
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
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} sidebarOpen={sidebarOpen} />

      <div className="flex flex-1">
       <Sidebar isOpen={sidebarOpen} />

         <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
           <ActiveTransportBanner />
           <DataModeBanner />
           <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
             {children}
           </main>

           <footer className="border-t border-border bg-card p-4 text-center flex-shrink-0">
             <p className="text-xs text-muted-foreground">
               MED-THERM Compliance Engine v0.1.0 • Built for regulatory compliance
             </p>
           </footer>
         </div>
      </div>
    </div>
  )
}

export default Layout
