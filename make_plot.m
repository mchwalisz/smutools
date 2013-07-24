%% Clear data
clear all;
% close all;
%% Configure
% Starhistogram2dt from scratch

% Parameters
opt.FontSize = 10;
opt.xdenom = 1e9; % Show in GHz
opt.xlabeltxt = 'Frequency (GHz)';
opt.savefigures = 0;

opt.dataAll = { ...
    'telos', ...
    'wispy', ...
    ...%     'fsv', ...
    };
opt.data = opt.dataAll;
% opt.data = {'temp'};

%% Do work
for ii=1:length(opt.data)
    %% Load data
    clearvars -except opt ii
    disp(['Loading up data: ' opt.data{ii} ...
        ' (' num2str(ii) '/' num2str(length(opt.data)) ')']);
    switch opt.data{ii}
        case 'telos'
            disp('Telos data...');
            p = crewcdf_telos( 'data_telos_XBTK0F1X.txt');
            % p.Name = '2013-7-9_20MHz-3GHz';
            opt.dir = 'Figs/';
            
        case 'wispy'
            disp('Wispy data...');
            p = crewcdf_wispy( ...
                'data_wispy_0_0.txt');
            % p.Name = '2013-7-9_20MHz-6GHz';
            opt.dir = 'Figs/';
            
        case 'fsv'
            disp('FSV data...');
            p = crewcdf_wispy( ...
                'data_fsv_192.168.10.250.fsv');
            % p.Name = '2013-7-10_20MHz-3GHz_FT440';
            opt.dir = 'Figs/';
            
    end
    lth = -95;  % Arbitrary detection threshold

    %% 1 Spectrogram
    titles.f1 = [p.Name, '_specgram'];
    f = figure('Name',titles.f1);
    crewcdf_imagesc(p,'Title',titles.f1);
    if opt.savefigures == 1
        savefig(f, [opt.dir, titles.f1])
    end
    
    %% 6 Heat map
    titles.f6 = [p.Name, '_heatmap'];
    f = figure('Name',titles.f6);
    crewcdf_heatmap(p, 'Title', titles.f6);
    hold on
    %     plot(p.CenterFreq/opt.xdenom, pMean,'c-');
%     plot(p.CenterFreq/opt.xdenom, pThreshold,'r-');
%     plot(p.CenterFreq/opt.xdenom, pThreshold + thadd,'m-');
    %     plot(p.CenterFreq/opt.xdenom, maxPower,'g:');
    %     plot(p.CenterFreq/opt.xdenom, minPower,'c:');
    line('XData', [p.CenterFreq(1)/opt.xdenom p.CenterFreq(end)/opt.xdenom], ...
        'YData', [lth lth], ...
        'LineStyle', '-', 'LineWidth', 1, 'Color','m');
%     legend( ... % 'Average over time', ...
%         'Noise floor', ...
%         ['Detection threshold (' num2str(thadd) 'dB)'] ...
%         );
    if opt.savefigures == 1
        savefig(f, [opt.dir, titles.f6])
    end
end