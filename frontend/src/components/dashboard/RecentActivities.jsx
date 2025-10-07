import React from "react";

const RecentActivities = ({ activities }) => {
  if (!activities || activities.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">📝 Atividades Recentes</h3>
        </div>
        <div className="card-content">
          <p className="text-center text-gray-500 dark:text-gray-400 py-8">
            Nenhuma atividade recente
          </p>
        </div>
      </div>
    );
  }

  const getTimeAgo = (timestamp) => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "agora mesmo";
    if (diffMins < 60) return `há ${diffMins} minuto${diffMins > 1 ? "s" : ""}`;
    if (diffHours < 24)
      return `há ${diffHours} hora${diffHours > 1 ? "s" : ""}`;
    return `há ${diffDays} dia${diffDays > 1 ? "s" : ""}`;
  };

  const getActivityColor = (type) => {
    const colors = {
      company_created:
        "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
      subscription_created:
        "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
      client_created:
        "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
      user_created:
        "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
    };
    return (
      colors[type] ||
      "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
    );
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">📝 Atividades Recentes</h3>
      </div>
      <div className="card-content">
        <div className="space-y-3">
          {activities.map((activity, index) => (
            <div
              key={index}
              className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center ${getActivityColor(
                  activity.type
                )}`}
              >
                <span className="text-xl">{activity.icon}</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {activity.title}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                  {activity.description}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  {getTimeAgo(activity.timestamp)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RecentActivities;
