import RepoAnalyticsDashboard from "@/components/repo-analytics-dashboard";
import type { Metadata } from "next";

export const metadata: Metadata = {
	title: "Codebase Analytics",
	description: "Analytics dashboard for public GitHub repositories",
};

export default function Page() {
	return <RepoAnalyticsDashboard />;
}
