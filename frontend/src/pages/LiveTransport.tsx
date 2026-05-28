import { useRef } from 'react'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Input,
} from '@/components/ui'
import { Play, Square, Radio, Thermometer, Upload, FileText, X, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { TemperatureChart } from '@/components/TemperatureChart'
import { TelemetryLineChart } from '@/components/TelemetryLineChart'
import { TELEMETRY_METRIC_BY_ID } from '@/lib/telemetry/metrics'
import { REGULATORY_CONSTANTS } from '@/lib/constants'
import { LiveAlertFeed } from '@/components/LiveTransport/LiveAlertFeed'
import { LIVE_SPEED_OPTIONS, type LiveScenario, type LiveSourceMode, type LiveSpeedMultiplier } from '@/lib/live/types'
import { useLiveTransport } from '@/lib/context/LiveTransportContext'

export function LiveTransportPage() {
  const {
    isRunning,
    scenario,
    sourceMode,
    speed,
    deviceId,
    logFileName,
    logLineCount,
    totalReplayBatches,
    ticks,
    alerts,
    tickIndex,
    startedAt,
    elapsedSec,
    isFinalizingReport,
    canStart,
    canResumeLog,
    scenarioLabels,
    temperatureData,
    fanData,
    humidityData,
    setScenario,
    setSourceMode,
    setSpeed,
    setDeviceId,
    startTransport,
    stopTransport,
    handleLogUpload,
    clearLogFile,
    formatElapsed,
  } = useLiveTransport()

  const fileInputRef = useRef<HTMLInputElement>(null)

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      void handleLogUpload(file)
    }
    e.target.value = ''
  }

  return (
    <div className="space-y-6 relative">
      {isFinalizingReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <Card className="w-full max-w-sm mx-4">
            <CardContent className="p-8 text-center">
              <Loader2 className="h-10 w-10 mx-auto mb-4 text-primary animate-spin" />
              <h3 className="text-lg font-semibold mb-2">Transport complete</h3>
              <p className="text-sm text-muted-foreground">
                Generating compliance report and opening Home…
              </p>
            </CardContent>
          </Card>
        </div>
      )}
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground font-heading flex items-center gap-2">
            <Radio className="h-8 w-8 text-primary" />
            Live Transport
          </h1>
          <p className="text-muted-foreground mt-1">
            Simulated telemetry or replay from a log file. Rule checks run on each tick; adjust speed
            with ×2 / ×5 / ×10 / ×25.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {isRunning && (
            <Badge variant="critical" className="animate-pulse gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500" />
              LIVE · ×{speed}
            </Badge>
          )}
          {startedAt && (
            <Badge variant="outline">
              {formatElapsed(elapsedSec)} · {tickIndex}
              {totalReplayBatches > 0 ? ` / ${totalReplayBatches}` : ''} ticks
            </Badge>
          )}
          {canResumeLog && (
            <Badge variant="secondary">Paused — resume available</Badge>
          )}
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium">Session control</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row flex-wrap gap-4 items-end">
            <div className="space-y-1 min-w-[200px]">
              <label htmlFor="live-page-device-id" className="text-xs text-muted-foreground">
                Device ID
              </label>
              <Input
                id="live-page-device-id"
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                disabled={isRunning}
                placeholder="MED-UNIT-…"
              />
            </div>

            <div className="space-y-1 min-w-[220px]">
              <label className="text-xs text-muted-foreground">Data source</label>
              <Select
                value={sourceMode}
                onValueChange={(v) => setSourceMode(v as LiveSourceMode)}
                disabled={isRunning}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="simulated">Built-in scenario</SelectItem>
                  <SelectItem value="log_file" disabled={!logFileName}>
                    Log file replay{logFileName ? '' : ' (upload first)'}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {sourceMode === 'simulated' && (
              <div className="space-y-1 min-w-[220px]">
                <label className="text-xs text-muted-foreground">Scenario</label>
                <Select
                  value={scenario}
                  onValueChange={(v) => setScenario(v as LiveScenario)}
                  disabled={isRunning}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(Object.keys(scenarioLabels) as LiveScenario[]).map((key) => (
                      <SelectItem key={key} value={key}>
                        {scenarioLabels[key]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Simulation speed</label>
              <div className="flex gap-1">
                {LIVE_SPEED_OPTIONS.map((mult) => (
                  <Button
                    key={mult}
                    type="button"
                    size="sm"
                    variant={speed === mult ? 'default' : 'outline'}
                    className="min-w-[3rem]"
                    onClick={() => setSpeed(mult as LiveSpeedMultiplier)}
                  >
                    ×{mult}
                  </Button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row flex-wrap gap-3 items-center pt-2 border-t border-border">
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.log"
              className="hidden"
              onChange={onFileChange}
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={isRunning}
              onClick={() => fileInputRef.current?.click()}
              className="touch-target"
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload log file
            </Button>

            {logFileName && (
              <div className="flex items-center gap-2 text-sm">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium truncate max-w-[200px]">{logFileName}</span>
                <Badge variant="secondary">{logLineCount} lines</Badge>
                {!isRunning && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={clearLogFile}
                    aria-label="Remove log file"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            )}

            <div className="sm:ml-auto">
              {!isRunning ? (
                canResumeLog ? (
                  <div className="grid grid-cols-2 gap-2">
                    <Button
                      onClick={() => startTransport(false)}
                      disabled={!canStart}
                      size="default"
                      className="touch-target h-10 items-center"
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Continue
                    </Button>
                    <Button
                      onClick={() => startTransport(true)}
                      variant="outline"
                      size="default"
                      className="touch-target h-10 items-center"
                    >
                      Restart
                    </Button>
                  </div>
                ) : (
                  <Button
                    onClick={() => startTransport(false)}
                    disabled={!canStart}
                    size="default"
                    className="touch-target h-10 items-center min-w-44"
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Start transport
                  </Button>
                )
              ) : (
                <Button
                  onClick={stopTransport}
                  variant="destructive"
                  size="default"
                  className="touch-target h-10 items-center min-w-44"
                >
                  <Square className="h-4 w-4 mr-2" />
                  Stop
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {!isRunning && ticks.length === 0 ? (
        <Card className="border-dashed border-border/80 bg-muted/20">
          <CardContent className="p-12 text-center">
            <Thermometer className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <h3 className="text-lg font-semibold mb-2">Ready to monitor</h3>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              Pick a <strong>scenario</strong> or <strong>upload a .txt log</strong>, set speed, then press{' '}
              <strong>Start transport</strong>. Charts update in real time; violations show with advice.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 space-y-6">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span
                className={cn(
                  'px-2 py-0.5 rounded',
                  sourceMode === 'log_file' ? 'bg-blue-100 dark:bg-blue-950/40' : 'bg-muted'
                )}
              >
                {sourceMode === 'log_file' ? `Replay: ${logFileName ?? 'log'}` : `Scenario: ${scenarioLabels[scenario]}`}
              </span>
            </div>
            <TemperatureChart
              data={temperatureData}
              safeRange={REGULATORY_CONSTANTS.safeTemperatureRange}
              title={`Live temperature · ${deviceId}`}
              showControls={false}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {fanData.length > 0 && (
                <TelemetryLineChart data={fanData} metric={TELEMETRY_METRIC_BY_ID.fan_speed} />
              )}
              {humidityData.length > 0 && (
                <TelemetryLineChart data={humidityData} metric={TELEMETRY_METRIC_BY_ID.humidity} />
              )}
            </div>
          </div>
          <LiveAlertFeed alerts={alerts} />
        </div>
      )}
    </div>
  )
}

export default LiveTransportPage
