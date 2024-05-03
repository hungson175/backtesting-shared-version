#include <iostream>
#include "Database.h"
#include "Utils.h"
#include "cstring"
#include "strategies/Sma.h"
#include "strategies/Psar.h"

int main(int, char **) {
    // Database db("Binance");
    // int array_size = 0;
    // double** res = db.get_data("BTCUSDT", "Binance",array_size);
    // std::vector<double> ts, open, high, low, close, volume;
    // std::tie(ts, open, high, low, close, volume) = rearrange_candles(res,"5m",array_size);

    // for (int i = 0; i < 10 ; i++ ) {
    //     printf("%f %f %f %f %f %f\n", ts[i], open[i], high[i], low[i], close[i], volume[i] );
    // }

    // printf("Size: %i\n",ts.size());
    // db.close_file();

    std::string symbol = "BTCUSDT";
    std::string exchange = "Binance";

    char *symbol_c = strcpy((char *) malloc(symbol.length() + 1), symbol.c_str());
    char *exchange_c = strcpy((char *) malloc(exchange.length() + 1), exchange.c_str());

    std::string timeframe = "5m";
    char *timeframe_c = strcpy((char *) malloc(timeframe.length() + 1), timeframe.c_str());
    Sma sma(exchange_c, symbol_c, timeframe_c, 0, 1630074127000);
    sma.execute_backtest(21,9);
    printf("%f | %f\n", sma.pnl, sma.max_dd);

//    std::string timeframe = "1h";
//    char *timeframe_c = strcpy((char *) malloc(timeframe.length() + 1), timeframe.c_str());
//    Psar psar(exchange_c, symbol_c, timeframe_c, 0, 1630074127000);
//    psar.execute_backtest(0.02, 0.02, 0.2);
//    printf("%f | %f\n", psar.pnl, psar.max_dd);



}
