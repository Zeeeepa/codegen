import React from 'react';
import { useRouter } from 'next/router';
import useSWR from 'swr';
import Header from '@/components/Header';
import Card from '@/components/Card';
import StatusBadge from '@/components/StatusBadge';
import Link from 'next/link';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function Home() {
  const router = useRouter();
  const { data, error, isLoading } = useSWR('/api/dashboard', fetcher);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        <main className="container mx-auto py-8 px-4">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading dashboard data...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        <main className="container mx-auto py-8 px-4">
          <div className="text-center py-12">
            <div className="bg-error text-white p-4 rounded-md inline-block">
              <p>Error loading dashboard data. Please try again later.</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      <main className="container mx-auto py-8 px-4">
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-bold">PR REVIEW BOT DASHBOARD</h1>
            <div className="flex space-x-4">
              <div className="text-sm">
                <span className="font-medium">Status: </span>
                <StatusBadge status={data.status} text={data.status} />
              </div>
              <div className="text-sm">
                <span className="font-medium">Repositories: </span>
                <span>{data.repositories_count}</span>
              </div>
              <div className="text-sm">
                <span className="font-medium">Last Check: </span>
                <span>{data.last_check}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Card title="RECENT ACTIVITY">
            <ul className="space-y-2">
              {data.recent_activity.map((activity, index) => (
                <li key={index} className="text-sm">• {activity}</li>
              ))}
            </ul>
          </Card>

          <Card title="REPOSITORY HEALTH">
            <ul className="space-y-2">
              {Object.entries(data.repository_health).map(([repo, health]) => (
                <li key={repo} className="text-sm flex items-center">
                  <StatusBadge 
                    status={health.toString().includes('error') || health.toString().includes('warning') ? 'warning' : 'success'} 
                    text="" 
                  />
                  <span className="ml-2">
                    <Link href={`/repository/${repo}`} className="hover:text-primary">
                      {repo}: {health}
                    </Link>
                  </span>
                </li>
              ))}
            </ul>
          </Card>
        </div>

        <Card title="ACTIVE BRANCHES">
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Repository</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Implements</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.active_branches.map((branch, index) => (
                  <tr key={index}>
                    <td className="px-4 py-2 whitespace-nowrap text-sm">{branch.repository}</td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm">{branch.implements}</td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm">
                      <StatusBadge status={branch.status} text={branch.status} />
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm">
                      {branch.status.includes('PR') ? (
                        <button className="text-primary hover:underline">[View PR]</button>
                      ) : (
                        <button className="text-primary hover:underline">[Details]</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <div className="mt-8">
          <Card title="ERROR LOG">
            <ul className="space-y-4">
              {data.errors.map((error, index) => (
                <li key={index} className="text-sm border-l-4 border-error pl-4 py-2">
                  <div className="flex items-start">
                    <StatusBadge 
                      status={error.message.includes('Warning') ? 'warning' : 'error'} 
                      text="" 
                    />
                    <div className="ml-2">
                      <p>{error.message}</p>
                      <p className="text-gray-600 text-xs mt-1">in {error.repository}: {error.details}</p>
                      <div className="mt-2 space-x-2">
                        <button className="text-xs text-primary hover:underline">[Expand Details]</button>
                        <button className="text-xs text-primary hover:underline">[Retry]</button>
                        <button className="text-xs text-primary hover:underline">[Dismiss]</button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </Card>
        </div>

        <div className="mt-8 text-center">
          <button className="btn btn-primary mx-2">[Settings]</button>
          <button className="btn btn-primary mx-2">[Run Manual Check]</button>
          <button className="btn btn-primary mx-2">[Generate Report]</button>
          <button className="btn btn-primary mx-2">[View Logs]</button>
        </div>
      </main>
    </div>
  );
}