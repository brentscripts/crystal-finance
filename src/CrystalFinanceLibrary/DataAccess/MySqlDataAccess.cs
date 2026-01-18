using System.Data;
using System.Linq;
using Dapper;
using MySql.Data.MySqlClient;

namespace CrystalFinanceLibrary.DataAccess;

/// <summary>
/// Provides basic MySQL data access using Dapper.
/// </summary>
public class MySqlDataAccess
{
    /// <summary>
    /// Executes a SQL query and returns the result set as a list of objects.
    /// </summary>
    /// <typeparam name="T">The type to map the result rows to.</typeparam>
    /// <typeparam name="U">The type of the parameters object.</typeparam>
    /// <param name="sqlStatement">The SQL query to execute.</param>
    /// <param name="parameters">The parameters used by the SQL query.</param>
    /// <param name="connectionString">The MySQL connection string.</param>
    /// <returns>A list of mapped result objects.</returns>
    public async Task<IEnumerable<T>> LoadDataAsync<T, U>(
      string sqlStatement,
      U parameters,
      string connectionString)
    {
        using var connection = new MySqlConnection(connectionString);

        var rows = await connection
            .QueryAsync<T>(sqlStatement, parameters)
            .ConfigureAwait(false);

        return rows;
    }

    /// <summary>
    /// Executes a SQL command that does not return data (INSERT, UPDATE, DELETE).
    /// </summary>
    /// <typeparam name="T">The type of the parameters object.</typeparam>
    /// <param name="sqlStatement">The SQL command to execute.</param>
    /// <param name="parameters">The parameters used by the SQL command.</param>
    /// <param name="connectionString">The MySQL connection string.</param>
    /// <remarks>
    /// WARNING: async void should generally be avoided except for event handlers.
    /// Consider changing this to Task so errors can be awaited and handled properly.
    /// </remarks>
    public async Task SaveDataAsync<T>(
      string sqlStatement,
      T parameters,
      string connectionString)
    {
        using(IDbConnection connection = new MySqlConnection(connectionString))
        {
            await connection
                .ExecuteAsync(sqlStatement, parameters)
                .ConfigureAwait(false);
        }
    }
}
