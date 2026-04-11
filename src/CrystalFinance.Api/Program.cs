using CrystalFinance.Api.Startup;
using CrystalFinance.Ui.Enums;
using CrystalFinanceLibrary.Data;
using CrystalFinanceLibrary.Logic;
using Dapper;
using System.Data;
using System.Runtime.Intrinsics.X86;

SqlMapper.AddTypeMap(typeof(TranSourceType), DbType.String);

var builder = WebApplication.CreateBuilder(args);

var connectionString = builder.Configuration.GetConnectionString("DefaultConnection") 
    ?? throw new InvalidOperationException("Connection string 'DefaultConnection' not found.");

builder.AddDependencies();
builder.AddAuthentication();
builder.Services.AddCorsPolicy(builder.Configuration);
builder.Services.AddScoped<TransactionImportService>();
builder.Services.AddScoped<IMySqlDataService, MySqlData>(sp =>
    new MySqlData(connectionString));

var app = builder.Build();

app.UseOpenApi();

app.UseHttpsRedirection();

app.UseCustomCors();

app.UseAuthentication();

app.UseAuthorization();

app.MapControllers();

app.Run();
