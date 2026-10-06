import { useEffect, useState } from 'react';
import { Users, FileText, BrainCircuit, CheckCircle2, Loader2 } from 'lucide-react';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';

export default function Dashboard() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);
    patients: 0,
    cases: 0,
    recentCases: [] as any[],
    pendingAi: 0,
    completed: 0
  });

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [patientsRes, casesRes] = await Promise.all([
        api.get('/patients/'),
        api.get('/cases/')
      ]);

      setStats({
        patients: patientsRes.data.length,
        cases: casesRes.data.length,
        recentCases: casesRes.data.slice(-5).reverse(),
        pendingAi: casesRes.data.filter((c: any) => c.status === 'UNDER_ANALYSIS').length,
        completed: casesRes.data.filter((c: any) => c.status === 'COMPLETED').length,
      });
    } catch (error) {
      console.error('Failed to load dashboard data', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const kpis = [
    { label: 'Total Patients', value: stats.patients, icon: Users },
    { label: 'Total Cases', value: stats.cases, icon: FileText },
    { label: 'Pending AI Reviews', value: stats.pendingAi, icon: BrainCircuit },
    { label: 'Completed Cases', value: stats.completed, icon: CheckCircle2 },
  ];

  if (loading) {
    return <div className="flex h-[60vh] items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-blue-600" /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Dashboard</h1>
          <p className="text-gray-500 mt-1">Welcome back, {user?.name}. Here's what's happening today.</p>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, index) => (
          <div key={index} className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-medium text-gray-500">{kpi.label}</p>
                <h3 className="text-2xl font-bold text-gray-900 mt-1">{kpi.value}</h3>
              </div>
              <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
                <kpi.icon className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Cases */}
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm overflow-hidden flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Recent Cases</h3>
          </div>
          <div className="space-y-4 flex-1 overflow-y-auto">
            {stats.recentCases.length === 0 ? (
              <div className="text-center text-gray-500 py-8">No cases yet.</div>
            ) : (
              stats.recentCases.map((caseItem: any) => (
                <div key={caseItem.id} className="flex items-start justify-between p-3 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-100 transition-colors cursor-pointer">
                  <div>
                    <p className="font-medium text-gray-900 text-sm">Patient #{caseItem.patient_id}</p>
                    <div className="flex items-center text-xs text-gray-500 mt-1">
                      <span>CASE-{caseItem.id}</span>
                      <span className="mx-1.5">•</span>
                      <span>{caseItem.case_type || 'General'}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700`}>
                      {caseItem.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
