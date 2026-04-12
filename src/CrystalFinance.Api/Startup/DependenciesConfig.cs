using CrystalFinance.Api.HealthChecks;
using CrystalFinanceLibrary.Data;
using CrystalFinanceLibrary.Logic;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Identity.Web;
using System.Text.Json.Serialization;

namespace CrystalFinance.Api.Startup;

public static class DependenciesConfig
{
    public static void AddDependencies(this WebApplicationBuilder builder)
    {
        builder.Services.AddControllers()
            .AddJsonOptions(options =>
            {
                options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter());
            });

        builder.Services.AddOpenApiServices();

        builder.Services.AddAuthorization();

        var connectionString = builder.Configuration.GetConnectionString("DefaultConnection")
            ?? throw new InvalidOperationException("Connection string 'DefaultConnection' not found.");

        builder.Services.AddScoped<TransactionImportService>();
        builder.Services.AddScoped<IMySqlDataService, MySqlData>(sp =>
            new MySqlData(connectionString));

        // Add health checks
        builder.Services.AddHealthChecks()
            .AddCheck("self", () => Microsoft.Extensions.Diagnostics.HealthChecks.HealthCheckResult.Healthy("API is running"), 
                tags: new[] { "live" })
            .AddCheck<MySqlHealthCheck>(
                "mysql", 
                failureStatus: Microsoft.Extensions.Diagnostics.HealthChecks.HealthStatus.Unhealthy,
                tags: new[] { "ready", "db" });

        // Register MySqlHealthCheck with connection string
        builder.Services.AddScoped(sp => new MySqlHealthCheck(connectionString));

        builder.Services.AddResponseCaching();
    }
}
