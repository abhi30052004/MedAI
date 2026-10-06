import { useEffect, useState } from 'react';
import { Users, FileText, BrainCircuit, CheckCircle2, ArrowUpRight, ArrowDownRight, Loader2, Database } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';

const chartData = [
  { name: 'Mon', cases: 4 },
  { name: 'Tue', cases: 7 },
  { name: 'Wed', cases: 5 },
  { name: 'Thu', cases: 10 },
  { name: 'Fri', cases: 8 },
  { name: 'Sat', cases: 2 },
  { name: 'Sun', cases: 3 },
];

export default function Dashboard() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    patients: 0,
    cases: 0,
    recentCases: [] as any[]
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
        recentCases: casesRes.data.slice(-5).reverse() // Get latest 5
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

  const handleSeedData = async () => {
    if (!window.confirm("This will create a sample patient and case. Continue?")) return;

    try {
      // 1. Create Patient
      const patientRes = await api.post('/patients/', {
        first_name: "Jane",
        last_name: "Doe",
        date_of_birth: "1985-05-15",
        gender: "Female",
        contact_information: "jane.doe@example.com",
        medical_history: "Hypertension",
        allergies: "Penicillin",
        current_medications: "Lisinopril 10mg",
        organization_id: user?.organization_id
      });

      // 2. Create Case
      await api.post('/cases/', {
        title: "Annual Checkup and Chest Pain",
        patient_id: patientRes.data.id,
        status: "NEW",
        symptoms: {
          "description": "Mild chest discomfort, fatigue"
        }
      });

      alert("Demo data created successfully!");
      loadDashboardData();
    } catch (error) {
      console.error(error);
      alert("Failed to seed demo data");
    }
  };

  const kpis = [
    { label: 'Total Patients', value: stats.patients, icon: Users, change: '+12%', trend: 'up' },
    { label: 'Active Cases', value: stats.cases, icon: FileText, change: '+5%', trend: 'up' },
    { label: 'Pending AI Reviews', value: '0', icon: BrainCircuit, change: '-2%', trend: 'down' },
    { label: 'Completed Cases', value: '0', icon: CheckCircle2, change: '+18%', trend: 'up' },
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
        {user?.role === 'admin' && (
          <button
            onClick={handleSeedData}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <Database className="w-4 h-4" />
            Seed Demo Data
          </button>
        )}
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
            <div className="mt-4 flex items-center text-sm">
              {kpi.trend === 'up' ? (
                <ArrowUpRight className="w-4 h-4 text-green-500 mr-1" />
              ) : (
                <ArrowDownRight className="w-4 h-4 text-red-500 mr-1" />
              )}
              <span className={kpi.trend === 'up' ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
                {kpi.change}
              </span>
              <span className="text-gray-400 ml-1">vs last month</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Cases by Day</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#6B7280', fontSize: 12 }} />
                <Tooltip
                  cursor={{ fill: '#F3F4F6' }}
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="cases" fill="#2563eb" radius={[4, 4, 0, 0]} barSize={32} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

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
