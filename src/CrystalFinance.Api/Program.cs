using CrystalFinance.Api.Startup;
using CrystalFinance.Ui.Enums;
using Dapper;
using System.Data;

SqlMapper.AddTypeMap(typeof(TranSourceType), DbType.String);

var builder = WebApplication.CreateBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("DefaultConnection") 
    ?? throw new InvalidOperationException("Connection string 'DefaultConnection' not found.");

builder.AddDependencies();
builder.AddAuthentication();
builder.Services.AddCorsPolicy(builder.Configuration);

var app = builder.Build();

app.UseOpenApi();

app.UseHttpsRedirection();

app.UseResponseCaching();

app.UseCustomCors();

app.UseAuthentication();

app.UseAuthorization();

app.MapControllers();

// Health check endpoints
app.MapHealthChecks("/health");                          // Overall health
app.MapHealthChecks("/health/live", new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions 
{ 
    Predicate = check => check.Tags.Contains("live")     // Liveness probe (K8s)
});
app.MapHealthChecks("/health/ready", new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions 
{ 
    Predicate = check => check.Tags.Contains("ready")    // Readiness probe (K8s) 
});

app.Run();
