function postprocessing
f = figure;
k = uicontrol(f,'Style','popupmenu');
data = readmatrix('radiationPattern_corrected_eplane_co_new.csv');
k.String = data(1,2:end)./1e9;

k.Callback = @selection;
    function selection(src, event)
        val = k.Value;
        s21 = data(2:end, val+1);
        
        s21_norm = s21 -max(s21);
        polarplot(deg2rad(data(2:end, 1)),s21_norm, 'LineWidth', 2)
        set(gca, 'rlim', [-40 0],...
            'ThetaZeroLocation', 'top')
    end
end