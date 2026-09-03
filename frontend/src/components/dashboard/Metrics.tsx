import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from 'recharts';
import { Briefcase, AlertTriangle, Clock, Activity, DollarSign, PenTool, Truck } from 'lucide-react';

const COLORS = ['#18181b', '#10b981', '#f59e0b', '#ef4444', '#64748b', '#06b6d4'];

interface EquipmentBreakdownItem {
  status: string;
  count: number;
}

interface DashboardJobMetrics {
  open_jobs: number;
  pending_approval: number;
  in_progress: number;
  on_hold: number;
  overdue: number;
  avg_completion_time_hours: number;
  actual_cost: number;
  estimated_cost: number;
}

interface DashboardFleetMetrics {
  utilization_percentage: number;
  in_use: number;
  total_equipment: number;
  pending_requisitions: number;
  equipment_utilization_breakdown: EquipmentBreakdownItem[];
}

interface TimeSeriesItem {
  date: string;
  jobs_created: number;
  jobs_completed: number;
}

interface DepartmentWorkloadItem {
  department_name: string;
  active_jobs: number;
}

export interface DashboardData {
  job_metrics: DashboardJobMetrics;
  fleet_metrics: DashboardFleetMetrics;
  timeseries_data: TimeSeriesItem[];
  department_workload: DepartmentWorkloadItem[];
}

interface MetricsProps {
  data: DashboardData;
}

export function MetricsCards({ data }: MetricsProps) {
  const jm = data.job_metrics;
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <MetricCard 
        title="Total Active Jobs" 
        value={jm.open_jobs} 
        subtitle={`${jm.pending_approval} Pending Approval`}
        icon={<Briefcase className="h-4 w-4 text-zinc-700" />} 
        trend={null}
      />
      <MetricCard 
        title="In Progress" 
        value={jm.in_progress} 
        subtitle={`${jm.on_hold} On Hold`}
        icon={<Activity className="h-4 w-4 text-emerald-600" />} 
        trend={null}
      />
      <MetricCard 
        title="Overdue Jobs" 
        value={jm.overdue} 
        subtitle={jm.overdue > 0 ? "Requires attention" : "All on schedule"}
        icon={<AlertTriangle className={`h-4 w-4 ${jm.overdue > 0 ? "text-rose-600" : "text-zinc-400"}`} />} 
        trend={null}
      />
      <MetricCard 
        title="Avg Completion Time" 
        value={`${jm.avg_completion_time_hours}h`} 
        subtitle="Shift execution latency"
        icon={<Clock className="h-4 w-4 text-amber-600" />} 
        trend={null}
      />
    </div>
  );
}

export function FleetMetricsCards({ data }: MetricsProps) {
  const fm = data.fleet_metrics;
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <MetricCard 
        title="Fleet Utilization" 
        value={`${fm.utilization_percentage}%`} 
        subtitle={`${fm.in_use} of ${fm.total_equipment} in use`}
        icon={<Truck className="h-4 w-4 text-zinc-800" />} 
        trend={null}
      />
      <MetricCard 
        title="Pending Requisitions" 
        value={fm.pending_requisitions} 
        subtitle="Awaiting allocation"
        icon={<PenTool className="h-4 w-4 text-amber-600" />} 
        trend={null}
      />
      <MetricCard 
        title="Cost Variance" 
        value={`$${(data.job_metrics.actual_cost - data.job_metrics.estimated_cost).toFixed(2)}`} 
        subtitle="Actual vs Estimated"
        icon={<DollarSign className="h-4 w-4 text-zinc-800" />} 
        trend={null}
      />
    </div>
  );
}

function MetricCard({ title, value, subtitle, icon, trend }: { title: string, value: string | number, subtitle: string, icon: React.ReactNode, trend: React.ReactNode }) {
  return (
    <div className="bg-white border border-zinc-200 rounded-lg p-4 shadow-2xs flex flex-col justify-between hover:border-zinc-300 transition-colors">
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">{title}</h4>
        <div className="p-1.5 bg-zinc-100 rounded-md border border-zinc-200/60">
          {icon}
        </div>
      </div>
      <div>
        <div className="text-2xl font-bold font-mono tracking-tight text-zinc-900">{value}</div>
        <div className="text-[11px] text-zinc-500 font-medium mt-1 flex justify-between items-center">
          <span>{subtitle}</span>
          {trend}
        </div>
      </div>
    </div>
  );
}

export function ChartsSection({ data }: MetricsProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      
      {/* Time Series */}
      <div className="bg-white border border-zinc-200 rounded-lg p-5 shadow-2xs h-80">
        <h4 className="text-xs font-semibold uppercase tracking-wider mb-4 text-zinc-700">Jobs Activity (Created vs Completed)</h4>
        <ResponsiveContainer width="100%" height="88%">
          <LineChart data={data.timeseries_data} margin={{ top: 5, right: 20, bottom: 25, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f4f4f5" />
            <XAxis dataKey="date" tick={{fontSize: 11, fill: '#71717a'}} tickLine={false} axisLine={false} />
            <YAxis tick={{fontSize: 11, fill: '#71717a'}} tickLine={false} axisLine={false} />
            <RechartsTooltip 
              contentStyle={{ borderRadius: '6px', border: '1px solid #e4e4e7', background: '#ffffff', color: '#09090b', fontSize: '12px' }}
            />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Line type="monotone" name="Created" dataKey="jobs_created" stroke="#18181b" strokeWidth={2.5} dot={{r: 3}} activeDot={{r: 5}} />
            <Line type="monotone" name="Completed" dataKey="jobs_completed" stroke="#10b981" strokeWidth={2.5} dot={{r: 3}} activeDot={{r: 5}} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Department Workload */}
      <div className="bg-white border border-zinc-200 rounded-lg p-5 shadow-2xs h-80">
        <h4 className="text-xs font-semibold uppercase tracking-wider mb-4 text-zinc-700">Active Workload by Department</h4>
        <ResponsiveContainer width="100%" height="88%">
          <BarChart data={data.department_workload} margin={{ top: 5, right: 20, bottom: 25, left: 0 }} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f4f4f5" />
            <XAxis type="number" tick={{fontSize: 11, fill: '#71717a'}} tickLine={false} axisLine={false} />
            <YAxis dataKey="department_name" type="category" width={120} tick={{fontSize: 10, fill: '#71717a'}} tickLine={false} axisLine={false} />
            <RechartsTooltip 
              cursor={{fill: '#f4f4f5'}}
              contentStyle={{ borderRadius: '6px', border: '1px solid #e4e4e7', background: '#ffffff', color: '#09090b', fontSize: '12px' }}
            />
            <Bar dataKey="active_jobs" name="Active Jobs" fill="#18181b" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Equipment Utilization Pie */}
      <div className="bg-white border border-zinc-200 rounded-lg p-5 shadow-2xs h-80 lg:col-span-2">
        <h4 className="text-xs font-semibold uppercase tracking-wider mb-4 text-zinc-700">Equipment Fleet Allocation Breakdown</h4>
        <ResponsiveContainer width="100%" height="88%">
          <PieChart>
            <Pie
              data={data.fleet_metrics.equipment_utilization_breakdown}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={4}
              dataKey="count"
              nameKey="status"
              label={(props: { payload?: { status?: string }; value?: number }) => `${props.payload?.status || ''}: ${props.value || 0}`}
            >
              {data.fleet_metrics.equipment_utilization_breakdown.map((_entry: EquipmentBreakdownItem, index: number) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <RechartsTooltip contentStyle={{ borderRadius: '6px', border: '1px solid #e4e4e7', background: '#ffffff', color: '#09090b', fontSize: '12px' }} />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}
