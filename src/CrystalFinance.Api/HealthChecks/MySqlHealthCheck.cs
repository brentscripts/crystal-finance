using Microsoft.Extensions.Diagnostics.HealthChecks;
using MySql.Data.MySqlClient;

namespace CrystalFinance.Api.HealthChecks;

/// <summary>
/// Custom health check for MySQL database connectivity.
/// </summary>
public class MySqlHealthCheck : IHealthCheck
{
    private readonly string _connectionString;

    public MySqlHealthCheck(string connectionString)
    {
        _connectionString = connectionString;
    }

    public async Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext context, CancellationToken cancellationToken = default)
    {
        try
        {
            using var connection = new MySqlConnection(_connectionString);
            await connection.OpenAsync(cancellationToken);
            
            using var command = connection.CreateCommand();
            command.CommandText = "SELECT 1";
            await command.ExecuteScalarAsync(cancellationToken);

            return HealthCheckResult.Healthy("MySQL database is accessible.");
        }
        catch (Exception ex)
        {
            return HealthCheckResult.Unhealthy($"MySQL database check failed: {ex.Message}");
        }
    }
}
