import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from 'recharts';
import { Briefcase, AlertTriangle, Clock, Activity, DollarSign, PenTool, Truck } from 'lucide-react';

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#64748b'];

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

interface DashboardData {
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
        icon={<Briefcase className="h-5 w-5 text-blue-500" />} 
        trend={null}
      />
      <MetricCard 
        title="In Progress" 
        value={jm.in_progress} 
        subtitle={`${jm.on_hold} On Hold`}
        icon={<Activity className="h-5 w-5 text-emerald-500" />} 
        trend={null}
      />
      <MetricCard 
        title="Overdue Jobs" 
        value={jm.overdue} 
        subtitle="Requires attention"
        icon={<AlertTriangle className="h-5 w-5 text-red-500" />} 
        trend={null}
      />
      <MetricCard 
        title="Avg Completion Time" 
        value={`${jm.avg_completion_time_hours}h`} 
        subtitle="Time from start to finish"
        icon={<Clock className="h-5 w-5 text-amber-500" />} 
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
        icon={<Truck className="h-5 w-5 text-indigo-500" />} 
        trend={null}
      />
      <MetricCard 
        title="Pending Requisitions" 
        value={fm.pending_requisitions} 
        subtitle="Awaiting processing"
        icon={<PenTool className="h-5 w-5 text-orange-500" />} 
        trend={null}
      />
      <MetricCard 
        title="Cost Variance" 
        value={`$${(data.job_metrics.actual_cost - data.job_metrics.estimated_cost).toFixed(2)}`} 
        subtitle="Actual vs Estimated"
        icon={<DollarSign className="h-5 w-5 text-emerald-500" />} 
        trend={null}
      />
    </div>
  );
}

function MetricCard({ title, value, subtitle, icon, trend }: { title: string, value: string | number, subtitle: string, icon: React.ReactNode, trend: React.ReactNode }) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-sm flex flex-col">
      <div className="flex justify-between items-start mb-2">
        <h4 className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</h4>
        <div className="p-2 bg-slate-50 dark:bg-slate-800 rounded-md">
          {icon}
        </div>
      </div>
      <div className="flex-1 flex flex-col justify-end">
        <div className="text-3xl font-bold text-slate-900 dark:text-white">{value}</div>
        <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex justify-between">
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
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-sm h-80">
        <h4 className="text-sm font-semibold mb-4 text-slate-800 dark:text-slate-200">Jobs Activity (Time Series)</h4>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.timeseries_data} margin={{ top: 5, right: 20, bottom: 25, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="date" tick={{fontSize: 12}} tickLine={false} axisLine={false} />
            <YAxis tick={{fontSize: 12}} tickLine={false} axisLine={false} />
            <RechartsTooltip 
              contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Line type="monotone" name="Created" dataKey="jobs_created" stroke="#0ea5e9" strokeWidth={3} dot={{r: 4}} activeDot={{r: 6}} />
            <Line type="monotone" name="Completed" dataKey="jobs_completed" stroke="#10b981" strokeWidth={3} dot={{r: 4}} activeDot={{r: 6}} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Department Workload */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-sm h-80">
        <h4 className="text-sm font-semibold mb-4 text-slate-800 dark:text-slate-200">Department Workload</h4>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data.department_workload} margin={{ top: 5, right: 20, bottom: 25, left: 0 }} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
            <XAxis type="number" tick={{fontSize: 12}} tickLine={false} axisLine={false} />
            <YAxis dataKey="department_name" type="category" width={100} tick={{fontSize: 12}} tickLine={false} axisLine={false} />
            <RechartsTooltip 
              cursor={{fill: '#f1f5f9'}}
              contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
            />
            <Bar dataKey="active_jobs" name="Active Jobs" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Equipment Utilization Pie */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-5 shadow-sm h-80">
        <h4 className="text-sm font-semibold mb-4 text-slate-800 dark:text-slate-200">Equipment Status</h4>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data.fleet_metrics.equipment_utilization_breakdown}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={5}
              dataKey="count"
              nameKey="status"
              label={(props: { payload?: { status?: string }; value?: number }) => `${props.payload?.status || ''}: ${props.value || 0}`}
            >
              {data.fleet_metrics.equipment_utilization_breakdown.map((_entry: EquipmentBreakdownItem, index: number) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <RechartsTooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}
